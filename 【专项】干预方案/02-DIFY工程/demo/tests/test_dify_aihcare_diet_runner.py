import importlib.util
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = TOOL_DIR / "dify_aihcare_diet_runner.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("dify_aihcare_diet_runner", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_final_plan(mismatch=False):
    meal_total_kcal = 999 if mismatch else 220
    return {
        "planName": "饮食健康处方",
        "planTitle": "控糖减重饮食方案",
        "planSummary": "测试摘要",
        "executionPoints": "测试执行要点",
        "groups": [
            {
                "groupTitle": "最近7天饮食执行菜谱",
                "groupType": "weeklyMealPlan",
                "groupSummary": "最近7天三餐执行安排。",
                "displayStyle": "weeklyMealPlan",
                "items": [
                    {
                        "itemType": "dailyMealPlan",
                        "day": day,
                        "title": f"第{day}天",
                        "content": "测试日",
                        "focusPoint": "测试",
                        "importance": "重点执行",
                        "dailyTotalKcal": meal_total_kcal,
                        "dailyTotalProteinG": 12,
                        "dailyTotalFatG": 8,
                        "dailyTotalCarbsG": 26,
                        "estimatedEnergyDeficitKcal": 300,
                        "meals": [
                            {
                                "mealName": "早餐",
                                "mealTotalKcal": meal_total_kcal,
                                "mealTotalProteinG": 12,
                                "mealTotalFatG": 8,
                                "mealTotalCarbsG": 26,
                                "foods": [
                                    {
                                        "name": "燕麦片",
                                        "amountG": 40,
                                        "kcal": 150,
                                        "proteinG": 5,
                                        "fatG": 3,
                                        "carbsG": 26,
                                    },
                                    {
                                        "name": "水煮鸡蛋",
                                        "amountG": 50,
                                        "kcal": 70,
                                        "proteinG": 7,
                                        "fatG": 5,
                                        "carbsG": 0,
                                    },
                                ],
                            }
                        ],
                    }
                    for day in range(1, 8)
                ],
            }
        ],
    }


class DifyAihcareDietRunnerTests(unittest.TestCase):
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
                            "metricRecordsLast1y": [{"metricName": "体重", "value": 83.4}],
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
            self.assertEqual(result.case_dir.name, "张三_饮食方案_20260519-101112")
            saved = json.loads((result.case_dir / "入参.json").read_text(encoding="utf-8"))
            inputs = saved["dify_payload"]["inputs"]
            self.assertEqual(inputs["planType"], "diet")
            self.assertEqual(saved["metadata"]["defaultEnvironment"], "prod")
            self.assertIsInstance(inputs["externalPatientInfo"], str)
            self.assertIsInstance(inputs["basicProfile"], str)
            self.assertIsInstance(inputs["metricRecordsLast1y"], str)
            self.assertNotIn("response_mode", inputs)
            self.assertNotIn("query", inputs)
            self.assertIn("python3 dify_aihcare_diet_runner.py run", saved["terminal_command"])
            self.assertIn("--env-name prod", saved["terminal_command"])

    def test_extract_final_plan_and_validate_nutrition(self):
        runner = load_runner()
        plan = sample_final_plan(mismatch=False)
        answer = "<think>保留</think><FINAL_PLAN_JSON>" + json.dumps(plan, ensure_ascii=False) + "</FINAL_PLAN_JSON>"

        extracted, error = runner.extract_final_plan(answer)
        summary = runner.validate_final_plan(extracted)

        self.assertIsNone(error)
        self.assertEqual(extracted["planTitle"], "控糖减重饮食方案")
        self.assertEqual(summary["weeklyDaysCount"], 7)
        self.assertEqual(summary["mismatches"], [])
        self.assertEqual(len(summary["zeroCarbFoods"]), 7)

    def test_validate_final_plan_reports_nutrition_mismatch(self):
        runner = load_runner()
        summary = runner.validate_final_plan(sample_final_plan(mismatch=True))

        self.assertGreater(len(summary["mismatches"]), 0)
        self.assertEqual(summary["mismatches"][0]["field"], "mealTotalKcal")

    def test_collect_streaming_events_builds_answer_nodes_and_metadata(self):
        runner = load_runner()
        stream = (
            'data: {"event":"node_started","data":{"id":"n1","title":"生成1~3天菜谱","node_type":"llm"}}\n\n'
            'data: {"event":"message","message_id":"msg-1","conversation_id":"conv-1","answer":"abc"}\n\n'
            'data: {"event":"node_finished","data":{"id":"n1","title":"生成1~3天菜谱","node_type":"llm","status":"succeeded","elapsed_time":1.2}}\n\n'
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
            case_dir = Path(temp_dir) / "张三_饮食方案_20260519-101112"
            case_dir.mkdir()
            (case_dir / "入参.json").write_text(
                json.dumps(
                    {
                        "metadata": {"patientName": "张三", "caseName": "饮食方案"},
                        "dify_payload": {
                            "inputs": {
                                "basicProfile": json.dumps(
                                    {
                                        "demographics": {"gender": "男", "age": 62},
                                        "healthInfo": {"currentDiseases": [{"name": "糖尿病"}]},
                                    },
                                    ensure_ascii=False,
                                ),
                                "diseaseProfile": json.dumps({"diabetesProfile": {"diabetesType": "2型糖尿病"}}, ensure_ascii=False),
                                "metricRecordsLast1y": json.dumps([{"metricName": "体重", "value": 83.4}], ensure_ascii=False),
                                "dietRecordsLast1y": json.dumps([{"foodName": "米饭", "intakeGrams": 100}], ensure_ascii=False),
                                "followupRecordsLast1y": json.dumps([{"followupType": "糖尿病随访"}], ensure_ascii=False),
                                "exerciseRecordsLast1y": json.dumps([{"exerciseItem": "慢走"}], ensure_ascii=False),
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
                "validationSummary": {"mismatches": [], "zeroCarbFoods": [], "weeklyDaysCount": 7, "errors": []},
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
            self.assertIn("控糖减重饮食方案", html)
            self.assertIn("快速定位", html)
            self.assertIn('href="#input-quality"', html)
            self.assertIn('id="run-overview"', html)
            self.assertIn("输入充分性", html)
            self.assertIn("有效信息概览", html)
            self.assertIn('class="input-detail"', html)
            self.assertIn("身高", html)
            self.assertIn("指标记录明细", html)
            self.assertIn("饮食记录明细", html)
            self.assertIn("用药记录明细", html)
            self.assertIn("慢病专项信息", html)
            self.assertIn("干预方案产出质量", html)
            self.assertIn("分组内容质检", html)
            self.assertIn("食谱完整性", html)
            self.assertIn("7天总计", html)
            self.assertIn("每天总计", html)
            self.assertIn("每日摄入", html)
            self.assertIn("每餐明细", html)
            self.assertIn("食物明细", html)
            self.assertIn("节点耗时", html)
            self.assertIn("慢节点 Top 5", html)
            self.assertIn('id="raw-data"', html)
            self.assertIn('<details class="raw-details">', html)
            self.assertNotIn('<details class="raw-details" open>', html)
            self.assertIn("timed out", html)
            self.assertNotIn("Bearer secret", html)

    def test_result_record_renders_html_when_final_plan_is_missing(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp_dir:
            case_dir = Path(temp_dir) / "未知患者_饮食方案_20260527-090344"
            case_dir.mkdir()
            (case_dir / "入参.json").write_text(
                json.dumps(
                    {
                        "metadata": {"patientName": "未知患者", "caseName": "饮食方案"},
                        "dify_payload": {"inputs": {}},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            record = {
                "startedAt": "2026-05-27T09:03:44+08:00",
                "endedAt": "2026-05-27T09:03:44+08:00",
                "request": {"headers": {"Authorization": "Bearer ***"}},
                "response": {"status": 301, "body": "Moved Permanently"},
                "events": [],
                "nodeRuns": [],
                "answer": "",
                "finalPlan": None,
                "validationSummary": None,
                "error": None,
            }

            _output_dir, raw_path, html_path = runner.write_result_record(
                case_dir,
                record,
                runner.parse_local_time("2026-05-27T09:03:44+08:00"),
                env_name="test",
            )

            self.assertTrue(raw_path.exists())
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("没有方案分组", html)
            self.assertIn("未生成 weeklyMealPlan", html)

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
