import importlib.util
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = TOOL_DIR / "dify_aihcare_sport_runner.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("dify_aihcare_sport_runner", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_final_plan(invalid=False):
    importance = "非常重要" if invalid else "重点执行"
    content = "" if invalid else "每周安排5天饭后快走，每次20-30分钟。"
    focus = "" if invalid else "优先改善餐后血糖波动，出现不适时停止运动。"
    return {
        "planName": "运动健康处方",
        "planTitle": "控糖减重运动管理方案",
        "planSummary": "围绕有氧运动、抗阻训练、碎片化执行和运动安全监测提供建议。",
        "executionPoints": "如出现低血糖表现、胸闷胸痛或明显头晕，应停止运动并联系医生。",
        "groups": [
            {
                "groupTitle": "有氧运动安排",
                "groupType": "adviceList",
                "groupSummary": "先建立规律有氧运动。",
                "displayStyle": "list",
                "items": [
                    {
                        "itemType": "advice",
                        "title": "饭后快走",
                        "content": content,
                        "focusPoint": focus,
                        "importance": importance,
                    }
                ],
            },
            {
                "groupTitle": "碎片化运动策略",
                "groupType": "adviceList",
                "groupSummary": "夜班时拆分运动。",
                "displayStyle": "list",
                "items": [
                    {
                        "itemType": "advice",
                        "title": "分段完成",
                        "content": "夜班或忙碌时拆成3次完成，每次8-10分钟。",
                        "focusPoint": "适配整块时间不足的场景。",
                        "importance": "常规建议",
                    }
                ],
            },
        ],
    }


class DifyAihcareSportRunnerTests(unittest.TestCase):
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
                            "exerciseRecordsLast1y": [{"exerciseItem": "慢走"}],
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
            self.assertEqual(result.case_dir.name, "张三_运动方案_20260519-101112")
            saved = json.loads((result.case_dir / "入参.json").read_text(encoding="utf-8"))
            inputs = saved["dify_payload"]["inputs"]
            self.assertEqual(inputs["planType"], "sport")
            self.assertEqual(saved["metadata"]["defaultEnvironment"], "prod")
            self.assertIsInstance(inputs["externalPatientInfo"], str)
            self.assertIsInstance(inputs["basicProfile"], str)
            self.assertIsInstance(inputs["exerciseRecordsLast1y"], str)
            self.assertNotIn("response_mode", inputs)
            self.assertNotIn("query", inputs)
            self.assertIn("python3 dify_aihcare_sport_runner.py run", saved["terminal_command"])
            self.assertIn("--env-name prod", saved["terminal_command"])

    def test_extract_final_plan_supports_tags_direct_json_and_wrapped_json(self):
        runner = load_runner()
        plan = sample_final_plan()
        tagged = "<FINAL_PLAN_JSON>" + json.dumps(plan, ensure_ascii=False) + "</FINAL_PLAN_JSON>"
        direct = json.dumps(plan, ensure_ascii=False)
        wrapped = json.dumps({"finalPlanJson": plan}, ensure_ascii=False)

        self.assertEqual(runner.extract_final_plan(tagged)[0]["planTitle"], "控糖减重运动管理方案")
        self.assertEqual(runner.extract_final_plan(direct)[0]["planTitle"], "控糖减重运动管理方案")
        self.assertEqual(runner.extract_final_plan(wrapped)[0]["planTitle"], "控糖减重运动管理方案")

    def test_validate_final_plan_reports_sport_structure_errors(self):
        runner = load_runner()

        ok_summary = runner.validate_final_plan(sample_final_plan())
        bad_summary = runner.validate_final_plan(sample_final_plan(invalid=True))
        empty_summary = runner.validate_final_plan({"groups": []})

        self.assertEqual(ok_summary["errors"], [])
        self.assertGreaterEqual(ok_summary["groupsCount"], 2)
        self.assertGreaterEqual(ok_summary["itemsCount"], 2)
        self.assertGreater(len(bad_summary["errors"]), 0)
        self.assertGreater(len(empty_summary["errors"]), 0)

    def test_collect_streaming_events_builds_answer_nodes_and_metadata(self):
        runner = load_runner()
        stream = (
            'data: {"event":"node_started","data":{"id":"n1","title":"生成运动方案","node_type":"llm"}}\n\n'
            'data: {"event":"message","message_id":"msg-1","conversation_id":"conv-1","answer":"abc"}\n\n'
            'data: {"event":"node_finished","data":{"id":"n1","title":"生成运动方案","node_type":"llm","status":"succeeded","elapsed_time":1.2}}\n\n'
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
            case_dir = Path(temp_dir) / "张三_运动方案_20260519-101112"
            case_dir.mkdir()
            (case_dir / "入参.json").write_text(
                json.dumps(
                    {
                        "metadata": {"patientName": "张三", "caseName": "运动方案"},
                        "dify_payload": {
                            "inputs": {
                                "basicProfile": json.dumps(
                                    {
                                        "demographics": {"gender": "男", "age": 62},
                                        "healthInfo": {"currentDiseases": [{"name": "糖尿病"}]},
                                        "lifestyle": {"dailySteps": 3000, "exerciseMethods": {"lowIntensity": ["慢走"]}},
                                    },
                                    ensure_ascii=False,
                                ),
                                "diseaseProfile": json.dumps({"diabetesProfile": {"diabetesType": "2型糖尿病"}}, ensure_ascii=False),
                                "metricRecordsLast1y": json.dumps([{"metricName": "起床血压", "value": "150/100"}], ensure_ascii=False),
                                "exerciseRecordsLast1y": json.dumps([{"exerciseItem": "慢走", "durationMinutes": 30}], ensure_ascii=False),
                                "followupRecordsLast1y": json.dumps([{"followupType": "糖尿病随访"}], ensure_ascii=False),
                                "dietRecordsLast1y": json.dumps([{"foodName": "米饭"}], ensure_ascii=False),
                                "medPickupRecords1y": json.dumps([{"drugName": "二甲双胍"}], ensure_ascii=False),
                                "activeControlGoals": json.dumps([{"metricName": "空腹血糖"}], ensure_ascii=False),
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
                "validationSummary": {"errors": [], "groupsCount": 2, "itemsCount": 2, "importantItemsCount": 1, "coverageWarnings": []},
                "error": {"type": "TimeoutError", "message": "timed out"},
            }

            output_dir, raw_path, html_path = runner.write_result_record(
                case_dir,
                record,
                runner.parse_local_time("2026-05-19T10:20:00+08:00"),
                env_name="prod",
            )

            self.assertEqual(output_dir.name, "20260519-102000_prod_no-messageid")
            self.assertEqual(raw_path.name, "20260519-102000_prod_no-messageid_raw-result.json")
            self.assertEqual(html_path.name, "20260519-102000_prod_no-messageid_result.html")
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            html = html_path.read_text(encoding="utf-8")
            self.assertEqual(raw["environment"]["name"], "prod")
            self.assertEqual(raw["request"]["headers"]["Authorization"], "Bearer ***")
            self.assertIn("环境：<strong>prod</strong>", html)
            self.assertIn("张三", html)
            self.assertIn("控糖减重运动管理方案", html)
            self.assertIn("快速定位", html)
            self.assertIn("输入充分性", html)
            self.assertIn("运动方式", html)
            self.assertIn("缺失提醒", html)
            self.assertIn("干预方案产出质量", html)
            self.assertIn("运动建议完整性", html)
            self.assertIn("安全提醒覆盖", html)
            self.assertIn("节点耗时", html)
            self.assertIn('<details class="raw-details">', html)
            self.assertNotIn('<details class="raw-details" open>', html)
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
