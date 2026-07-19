import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "clean_obesity_food_guide_for_dify.py"
SPEC = importlib.util.spec_from_file_location("food_guide_cleaner", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BuildDocumentsTest(unittest.TestCase):
    def test_splits_core_recipes_and_reference_sections_with_formal_titles(self):
        pages = {
            3: "成人肥胖食养指南\n一、前言\n核心原则\n1\n",
            21: "附录 2 常见食物交换表\n19\n",
            22: "附录 3 不同地区食谱示例\n一、东北地区\n20\n",
            62: "七、华南地区\n60\n",
            63: "附录 4 成人肥胖患者食养方举例\n61\n",
            70: "附录 6 常见身体活动强度系数\n68\n",
        }

        documents = MODULE.build_documents(pages)

        self.assertEqual(len(documents), 3)
        self.assertEqual(
            documents[0]["title"],
            "成人肥胖食养指南（国家卫生健康委办公厅，2024年版）·核心原则与食物选择",
        )
        self.assertIn("一、前言", documents[0]["content"])
        self.assertNotIn("不同地区食谱示例", documents[0]["content"])
        self.assertIn("不同地区食谱示例", documents[1]["content"])
        self.assertNotIn("一、前言", documents[1]["content"])
        self.assertIn("成人肥胖患者食养方举例", documents[2]["content"])
        self.assertNotIn("东北地区", documents[2]["content"])
        self.assertNotRegex(documents[0]["content"], r"\n1\n")


if __name__ == "__main__":
    unittest.main()
