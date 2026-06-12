import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TOOL_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = TOOL_DIR / "dify_aihcare_health_weekly_report_runner.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("dify_aihcare_health_weekly_report_runner", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_final_plan(invalid=False):
    importance = "非常重要" if invalid else "重点执行"
    content = "" if invalid else "本周记录显示血糖和血压仍需关注，下周继续补齐空腹、餐后血糖和血压记录。"
    focus = "" if invalid else "近7天记录是阶段性总结，连续异常需反馈医生或健管师。"
    return {
        "planName": "健康周报",
        "planTitle": "最近7天健康情况总结",
        "planSummary": "围绕指标变化、饮食运动执行、风险提醒和下周关注点提供总结。",
        "executionPoints": "先看指标是否连续异常，再看饮食运动记录是否稳定。",
        "groups": [
            {
                "groupTitle": "指标变化总结",
                "groupType": "adviceList",
                "groupSummary": "总结最近7天指标变化。",
                "displayStyle": "list",
                "items": [
                    {
                        "itemType": "advice",
                        "title": "关注血糖血压变化",
                        "content": content,
                        "focusPoint": focus,
                        "importance": importance,
                    }
                ],
            }
        ],
    }


class DifyAihcareHealthWeeklyReportRunnerTests(unittest.TestCase):
    def test_prepare_input_writes_case_and_stringifies_inputs(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            source = tmp_path / "raw.json"
            source.write_text(
                json.dumps(
                    {
                        "inputs": {
                            "externalPatientInfo": {"patientName": "张三"},
                            "basicProfile": {"demographics": {"age": 62}},
                            "metricRecordsLast1y": [{"recordDate": "2026-05-29", "metricName": "血压", "value": "148/92"}],
                            "response_mode": "blocking",
                            "query": "旧 query",
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = runner.prepare_input_file(
                source,
                tmp_path,
                env_name="prod",
                now=runner.parse_local_time("2026-05-19T10:11:12+08:00"),
            )

            self.assertEqual(result.patient_name, "张三")
            self.assertEqual(result.case_dir.name, "张三_健康周报_20260519-101112")
            saved = json.loads((result.case_dir / "入参.json").read_text(encoding="utf-8"))
            inputs = saved["dify_payload"]["inputs"]
            self.assertEqual(inputs["planType"], "report")
            self.assertEqual(saved["metadata"]["caseName"], "健康周报")
            self.assertIsInstance(inputs["externalPatientInfo"], str)
            self.assertIsInstance(inputs["basicProfile"], str)
            self.assertNotIn("response_mode", inputs)
            self.assertNotIn("query", inputs)
            self.assertIn("python3 dify_aihcare_health_weekly_report_runner.py run", saved["terminal_command"])
            self.assertIn("--env-name prod", saved["terminal_command"])

    def test_extract_final_plan_supports_tags_direct_json_and_wrapped_json(self):
        runner = load_runner()
        plan = sample_final_plan()
        tagged = "<FINAL_PLAN_JSON>" + json.dumps(plan, ensure_ascii=False) + "</FINAL_PLAN_JSON>"
        direct = json.dumps(plan, ensure_ascii=False)
        wrapped = json.dumps({"finalPlanJson": plan}, ensure_ascii=False)

        self.assertEqual(runner.extract_final_plan(tagged)[0]["planTitle"], "最近7天健康情况总结")
        self.assertEqual(runner.extract_final_plan(direct)[0]["planTitle"], "最近7天健康情况总结")
        self.assertEqual(runner.extract_final_plan(wrapped)[0]["planTitle"], "最近7天健康情况总结")

    def test_validate_final_plan_reports_health_weekly_report_structure_errors(self):
        runner = load_runner()

        ok_summary = runner.validate_final_plan(sample_final_plan())
        bad_summary = runner.validate_final_plan(sample_final_plan(invalid=True))
        empty_summary = runner.validate_final_plan({"groups": []})

        self.assertEqual(ok_summary["errors"], [])
        self.assertEqual(ok_summary["groupsCount"], 1)
        self.assertEqual(ok_summary["itemsCount"], 1)
        self.assertGreater(len(bad_summary["errors"]), 0)
        self.assertGreater(len(empty_summary["errors"]), 0)

    def test_collect_streaming_events_builds_answer_nodes_and_metadata(self):
        runner = load_runner()
        stream = (
            'data: {"event":"node_started","data":{"id":"n1","title":"生成健康周报","node_type":"llm"}}\n\n'
            'data: {"event":"message","message_id":"msg-1","conversation_id":"conv-1","answer":"abc"}\n\n'
            'data: {"event":"node_finished","data":{"id":"n1","title":"生成健康周报","node_type":"llm","status":"succeeded","elapsed_time":1.2}}\n\n'
            'data: {"event":"message_end","message_id":"msg-1","conversation_id":"conv-1","metadata":{"usage":{"total_tokens":12}}}\n\n'
        )
        record = runner.empty_record("POST", "https://example.test", {"Authorization": "Bearer secret"}, {})

        runner.collect_curl_response(record, stream + "\n__DIFY_HTTP_STATUS__:200\n", "")

        self.assertEqual(record["response"]["status"], 200)
        self.assertEqual(record["answer"], "abc")
        self.assertEqual(record["messageId"], "msg-1")
        self.assertEqual(record["conversationId"], "conv-1")
        self.assertEqual(record["messageEndMetadata"]["usage"]["total_tokens"], 12)
        self.assertEqual(record["nodeRuns"][0]["status"], "succeeded")

    def test_result_record_masks_authorization_and_renders_html_without_response(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir) / "张三_健康周报_20260519-101112"
            case_dir.mkdir()
            (case_dir / "入参.json").write_text(
                json.dumps(
                    {
                        "metadata": {"patientName": "张三", "caseName": "健康周报"},
                        "dify_payload": {
                            "inputs": {
                                "basicProfile": json.dumps({"demographics": {"gender": "男", "age": 62}}, ensure_ascii=False),
                                "metricRecordsLast1y": json.dumps([{"recordDate": "2026-05-29", "metricName": "血压", "value": "148/92"}], ensure_ascii=False),
                                "dietRecordsLast1y": json.dumps([{"recordDate": "2026-05-28", "description": "外卖"}], ensure_ascii=False),
                                "exerciseRecordsLast1y": json.dumps([{"recordDate": "2026-05-28", "exerciseType": "散步"}], ensure_ascii=False),
                            }
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            record = {
                "startedAt": "2026-05-19T10:20:00+08:00",
                "endedAt": "2026-05-19T10:21:00+08:00",
                "request": {"headers": {"Authorization": "Bearer ***"}},
                "response": None,
                "events": [],
                "nodeRuns": [],
                "answer": "",
                "finalPlan": sample_final_plan(),
                "validationSummary": {"errors": [], "groupsCount": 1, "itemsCount": 1, "importantItemsCount": 1, "coverageWarnings": []},
                "error": {"type": "TimeoutError", "message": "timed out"},
            }

            output_dir, raw_path, html_path = runner.write_result_record(
                case_dir,
                record,
                runner.parse_local_time("2026-05-19T10:20:00+08:00"),
                env_name="prod",
            )

            self.assertEqual(output_dir.name, "20260519-102000_prod_no-messageid")
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            html = html_path.read_text(encoding="utf-8")
            self.assertEqual(raw["environment"]["name"], "prod")
            self.assertEqual(raw["request"]["headers"]["Authorization"], "Bearer ***")
            self.assertIn("环境：<strong>prod</strong>", html)
            self.assertIn("张三", html)
            self.assertIn("最近7天健康情况总结", html)
            self.assertIn("指标变化总结", html)
            self.assertIn("timed out", html)
            self.assertNotIn("Bearer secret", html)

    def test_resolve_api_key_prefers_environment_specific_variable(self):
        runner = load_runner()
        with mock.patch.dict(
            "os.environ",
            {"DIFY_API_KEY": "generic", "DIFY_API_KEY_PROD": "prod-secret"},
            clear=True,
        ):
            self.assertEqual(runner.resolve_api_key(None, "prod"), "prod-secret")
            self.assertEqual(runner.resolve_api_key("explicit", "prod"), "explicit")


if __name__ == "__main__":
    unittest.main()
