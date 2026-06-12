import importlib.util
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = PROJECT_ROOT / "健康周报" / "DIFY工程-AI干预方案-健康周报"
NODE1_PATH = PROJECT_DIR / "节点1-入参拆包与基础清洗" / "代码-入参拆包与基础清洗.py"
NODE2_PATH = PROJECT_DIR / "节点2-素材摘要" / "代码-保护素材摘要LLM出参.py"
NODE5_PATH = PROJECT_DIR / "节点5-组装最终JSON+校验兜底" / "代码-组装最终JSON+校验兜底.py"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HealthWeeklyReportWorkflowCodeNodeTests(unittest.TestCase):
    def test_node1_extracts_recent_7d_records_from_latest_record_date(self):
        node1 = load_module(NODE1_PATH, "health_weekly_report_node1")

        result = node1.main(
            metricRecordsLast1y=json.dumps(
                [
                    {"recordDate": "2026-05-01", "metricName": "空腹血糖", "value": 7.2},
                    {"recordDate": "2026-05-24", "metricName": "空腹血糖", "value": 8.1},
                    {"recordDate": "2026-05-29", "metricName": "血压", "value": "148/92"},
                ],
                ensure_ascii=False,
            ),
            dietRecordsLast1y=json.dumps([{"recordDate": "2026-05-27", "description": "无糖早餐"}], ensure_ascii=False),
        )

        metric_context = json.loads(result["metricTrendContext"])
        input_stats = json.loads(result["inputStats"])
        recent_metrics = metric_context["metricRecordsRecent7d"]

        self.assertEqual(result["planType"], "report")
        self.assertEqual(input_stats["reportWindow"]["referenceDate"], "2026-05-29")
        self.assertEqual(input_stats["recent7dMetricRecordsCount"], 2)
        self.assertEqual([item["recordDate"] for item in recent_metrics], ["2026-05-24", "2026-05-29"])

    def test_node2_extracts_json_from_llm_text_and_falls_back(self):
        node2 = load_module(NODE2_PATH, "health_weekly_report_node2")

        result = node2.main(
            text='前文 {"metricTrendSummary":"血糖偏高","dietExerciseSummary":"饮食记录不足","riskAndFollowupSummary":"暂无急性不适"} 后文'
        )
        fallback = node2.main(text="not json")

        self.assertEqual(result["metricTrendSummary"], "血糖偏高")
        self.assertIn("materialSummaryBundleText", result)
        self.assertIn("近7天指标记录不足", fallback["metricTrendSummary"])

    def test_node5_extracts_json_and_normalizes_importance(self):
        node5 = load_module(NODE5_PATH, "health_weekly_report_node5")
        groups_text = """
        {
          "groups": [
            {
              "groupTitle": "指标变化总结",
              "groupType": "adviceList",
              "groupSummary": "总结最近7天指标变化。",
              "displayStyle": "list",
              "dietPlanGoalLabel": "",
              "goalBasis": "近7天有血糖和血压记录。",
              "items": [
                {
                  "itemType": "advice",
                  "title": "关注血糖血压变化",
                  "content": "本周记录显示血糖和血压仍需关注，下周继续补齐监测记录。",
                  "focusPoint": "近7天记录是阶段性总结。",
                  "importance": "非常重要"
                }
              ]
            }
          ]
        }
        """

        result = node5.main(
            planHeader=json.dumps(
                {
                    "planName": "健康周报",
                    "planTitle": "最近7天健康情况总结",
                    "planSummary": "围绕最近7天健康情况生成总结。",
                    "executionPoints": "补齐记录并关注连续异常。",
                },
                ensure_ascii=False,
            ),
            groups=groups_text,
        )

        plan = json.loads(result["finalPlanJsonText"])
        item = plan["groups"][0]["items"][0]
        self.assertEqual(result["validationErrorsCount"], 0)
        self.assertEqual(item["importance"], "常规建议")
        self.assertEqual(item["day"], "")
        self.assertEqual(item["meals"], [])

    def test_node5_returns_renderable_fallback_when_groups_are_empty(self):
        node5 = load_module(NODE5_PATH, "health_weekly_report_node5_fallback")

        result = node5.main(planHeader="not json", groups=json.dumps({"groups": []}, ensure_ascii=False))
        plan = json.loads(result["finalPlanJsonText"])

        self.assertEqual(result["validationErrorsCount"], 0)
        self.assertEqual(plan["planName"], "健康周报")
        self.assertEqual(plan["groups"][0]["groupTitle"], "本周健康概览")
        self.assertIn("没关系", plan["groups"][0]["items"][0]["content"])

    def test_node5_reports_validation_errors_for_missing_items(self):
        node5 = load_module(NODE5_PATH, "health_weekly_report_node5_validation")
        bad_groups = {
            "groups": [
                {
                    "groupTitle": "饮食执行总结",
                    "groupType": "adviceList",
                    "groupSummary": "测试。",
                    "displayStyle": "list",
                    "items": [],
                }
            ]
        }

        result = node5.main(
            planHeader=json.dumps(
                {
                    "planName": "健康周报",
                    "planTitle": "测试",
                    "planSummary": "测试",
                    "executionPoints": "测试",
                },
                ensure_ascii=False,
            ),
            groups=json.dumps(bad_groups, ensure_ascii=False),
        )

        self.assertGreater(result["validationErrorsCount"], 0)
        self.assertIn("items 必须是非空数组", "\n".join(result["validationErrors"]))


if __name__ == "__main__":
    unittest.main()
