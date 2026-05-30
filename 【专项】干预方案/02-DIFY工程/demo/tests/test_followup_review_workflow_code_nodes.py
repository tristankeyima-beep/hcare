import importlib.util
import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_DIR = PROJECT_ROOT / "复诊复查指导" / "DIFY工程-AI干预方案-复诊复查指导"
NODE5_PATH = PROJECT_DIR / "节点5-组装最终JSON+校验兜底" / "代码-组装最终JSON+校验兜底.py"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FollowupReviewWorkflowCodeNodeTests(unittest.TestCase):
    def test_node5_extracts_json_from_llm_text_and_normalizes_importance(self):
        node5 = load_module(NODE5_PATH, "followup_review_node5")
        groups_text = """
        下面是结果：
        {
          "groups": [
            {
              "groupTitle": "复查项目安排",
              "groupType": "adviceList",
              "groupSummary": "按慢病风险安排近期复查。",
              "displayStyle": "list",
              "dietPlanGoalLabel": "",
              "goalBasis": "近期餐后血糖偏高，需要复查糖化血红蛋白。",
              "items": [
                {
                  "itemType": "advice",
                  "title": "复查糖化血红蛋白",
                  "content": "未来2-4周内预约复查糖化血红蛋白、空腹血糖和血脂。",
                  "focusPoint": "用于判断近阶段控糖和血脂管理效果，并辅助医生调整治疗方案。",
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
                    "planName": "复诊复查指导",
                    "planTitle": "个性化复诊复查安排",
                    "planSummary": "围绕复诊时间、复查项目和异常就医触发提供指导。",
                    "executionPoints": "优先完成重点复查项目，并把结果回传给健管师。",
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
        self.assertEqual(plan["groups"][0]["dietPlanGoalLabel"], "")

    def test_node5_returns_renderable_fallback_when_groups_are_empty(self):
        node5 = load_module(NODE5_PATH, "followup_review_node5_fallback")

        result = node5.main(planHeader="not json", groups=json.dumps({"groups": []}, ensure_ascii=False))
        plan = json.loads(result["finalPlanJsonText"])

        self.assertEqual(result["validationErrorsCount"], 0)
        self.assertEqual(plan["planName"], "复诊复查指导")
        self.assertEqual(plan["groups"][0]["groupTitle"], "复诊复查总原则")
        self.assertEqual(plan["groups"][0]["items"][0]["importance"], "重点执行")

    def test_node5_reports_validation_errors_for_missing_required_content(self):
        node5 = load_module(NODE5_PATH, "followup_review_node5_validation")
        bad_groups = {
            "groups": [
                {
                    "groupTitle": "异常就医触发",
                    "groupType": "adviceList",
                    "groupSummary": "识别需要提前就医的情况。",
                    "displayStyle": "list",
                    "items": [],
                }
            ]
        }

        result = node5.main(
            planHeader=json.dumps(
                {
                    "planName": "复诊复查指导",
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
