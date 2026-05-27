import importlib.util
import json
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
NODE4_PATH = PROJECT_DIR / "节点4-生成7天菜谱group" / "代码-格式化7天菜谱group.py"
NODE6_PATH = PROJECT_DIR / "节点6-组装最终JSON+校验兜底" / "代码-组装最终JSON+校验兜底.py"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_meal_plan_group():
    return {
        "mealPlanGroup": {
            "groupTitle": "最近7天饮食执行菜谱",
            "groupType": "weeklyMealPlan",
            "groupSummary": "最近7天三餐执行安排。",
            "displayStyle": "weeklyMealPlan",
            "items": [
                {
                    "itemType": "dailyMealPlan",
                    "day": 1,
                    "title": "第1天",
                    "content": "控糖减重基础日",
                    "focusPoint": "测试浮点求和",
                    "importance": "重点执行",
                    "meals": [
                        {
                            "mealName": "早餐",
                            "foods": [
                                {"name": "燕麦片", "amountG": 40, "kcal": 150, "proteinG": 5, "fatG": 3, "carbsG": 27},
                                {"name": "脱脂牛奶", "amountG": 240, "kcal": 80, "proteinG": 8, "fatG": 0, "carbsG": 12},
                                {"name": "核桃", "amountG": 10, "kcal": 65, "proteinG": 1.5, "fatG": 6.5, "carbsG": 1.4},
                                {"name": "蓝莓", "amountG": 50, "kcal": 28, "proteinG": 0.4, "fatG": 0.2, "carbsG": 7},
                            ],
                        },
                        {
                            "mealName": "午餐",
                            "foods": [
                                {"name": "荞麦面", "amountG": 200, "kcal": 280, "proteinG": 10, "fatG": 2, "carbsG": 55},
                                {"name": "鸡胸肉", "amountG": 100, "kcal": 165, "proteinG": 31, "fatG": 3.6, "carbsG": 0},
                                {"name": "西兰花", "amountG": 150, "kcal": 50, "proteinG": 4, "fatG": 0.5, "carbsG": 10},
                                {"name": "胡萝卜", "amountG": 80, "kcal": 33, "proteinG": 0.8, "fatG": 0.2, "carbsG": 8},
                                {"name": "橄榄油", "amountG": 5, "kcal": 45, "proteinG": 0, "fatG": 5, "carbsG": 0},
                            ],
                        },
                        {
                            "mealName": "晚餐",
                            "foods": [
                                {"name": "糙米饭", "amountG": 150, "kcal": 240, "proteinG": 5, "fatG": 2, "carbsG": 50},
                                {"name": "蒸鲈鱼", "amountG": 120, "kcal": 140, "proteinG": 22, "fatG": 5, "carbsG": 0},
                                {"name": "清炒菠菜", "amountG": 200, "kcal": 60, "proteinG": 5, "fatG": 1, "carbsG": 10},
                                {"name": "豆腐", "amountG": 50, "kcal": 40, "proteinG": 4, "fatG": 2, "carbsG": 2},
                                {"name": "芝麻油", "amountG": 3, "kcal": 27, "proteinG": 0, "fatG": 3, "carbsG": 0},
                            ],
                        },
                        {
                            "mealName": "加餐",
                            "foods": [
                                {"name": "无糖酸奶", "amountG": 100, "kcal": 50, "proteinG": 5, "fatG": 0, "carbsG": 7},
                            ],
                        },
                    ],
                }
            ],
        }
    }


class DietWorkflowCodeNodeTests(unittest.TestCase):
    def test_node4_rounds_recalculated_nutrition_totals(self):
        node4 = load_module(NODE4_PATH, "diet_node4")

        result = node4.main(mealPlanGroup=json.dumps(sample_meal_plan_group(), ensure_ascii=False))
        group = json.loads(result["mealPlanGroup"])
        item = group["items"][0]

        self.assertEqual(item["dailyTotalProteinG"], 101.7)
        self.assertEqual(item["dailyTotalFatG"], 34)

    def test_node4_handles_integer_only_totals(self):
        node4 = load_module(NODE4_PATH, "diet_node4_integer_totals")
        self.assertEqual(node4._sum_number([{"value": 1}, {"value": 2}], "value"), 3)

        meal_plan_group = sample_meal_plan_group()
        meals = meal_plan_group["mealPlanGroup"]["items"][0]["meals"]
        meals[0]["foods"] = [
            {"name": "糙米饭", "amountG": 150, "kcal": 180, "proteinG": 4, "fatG": 1, "carbsG": 38},
            {"name": "豆腐", "amountG": 120, "kcal": 120, "proteinG": 12, "fatG": 6, "carbsG": 4},
        ]
        meals[1]["foods"] = [
            {"name": "鸡胸肉", "amountG": 100, "kcal": 165, "proteinG": 31, "fatG": 3, "carbsG": 0},
        ]
        meals[2]["foods"] = [
            {"name": "小米饭", "amountG": 150, "kcal": 180, "proteinG": 4, "fatG": 1, "carbsG": 38},
        ]
        meals[3]["foods"] = [
            {"name": "无糖酸奶", "amountG": 100, "kcal": 50, "proteinG": 5, "fatG": 0, "carbsG": 7},
        ]

        result = node4.main(mealPlanGroup=json.dumps(meal_plan_group, ensure_ascii=False))
        group = json.loads(result["mealPlanGroup"])
        item = group["items"][0]

        self.assertEqual(item["dailyTotalKcal"], 695)
        self.assertIsInstance(item["dailyTotalKcal"], int)

    def test_node6_rounds_recalculated_nutrition_totals(self):
        node6 = load_module(NODE6_PATH, "diet_node6")

        result = node6.main(
            planHeader=json.dumps({"planName": "饮食健康处方", "planTitle": "测试", "planSummary": "测试", "executionPoints": "测试"}, ensure_ascii=False),
            mealPlanGroup=json.dumps(sample_meal_plan_group(), ensure_ascii=False),
        )
        plan = json.loads(result["finalPlanJsonText"])
        item = plan["groups"][0]["items"][0]

        self.assertEqual(item["dailyTotalProteinG"], 101.7)
        self.assertEqual(item["dailyTotalFatG"], 34)


if __name__ == "__main__":
    unittest.main()
