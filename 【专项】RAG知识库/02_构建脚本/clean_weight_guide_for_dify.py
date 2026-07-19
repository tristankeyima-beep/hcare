"""Create a Dify-oriented Markdown extraction of the supplied weight-management guide.

The source PDF is an academic two-column layout.  This extractor reads each
column independently, removes publication furniture, and excludes bibliography
content.  It never alters the original PDF.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
import os
from pathlib import Path

from pypdf import PdfReader


SPECIAL_DIR = Path(__file__).resolve().parents[1]
SOURCE = SPECIAL_DIR / "01_知识库文档/中国成人体重管理指南_2025原始PDF.pdf"
OUTPUT = SPECIAL_DIR / "01_知识库文档/中国成人体重管理指南_2025_Dify清洗版.md"
PDFTOTEXT = Path(
    os.environ.get(
        "PDFTOTEXT_PATH",
        "/Users/Tristan/.cache/codex-runtimes/codex-primary-runtime/"
        "dependencies/native/poppler/poppler/bin/pdftotext",
    )
)


def normalise(text: str) -> str:
    """Remove PDF extraction artefacts while retaining Chinese and Latin text."""
    text = unicodedata.normalize("NFKC", text)
    text = (
        text.replace("ꎬ", "，")
        .replace("ꎮ", "。")
        .replace("ꎻ", "；")
        .replace("􀅰", "·")
        .replace("￣", "-")
        .replace("̄", "-")
        .replace("\u00ad", "")
    )
    text = re.sub(r"fmx_[A-Za-z0-9_-]+", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff，。；：、（(])\s+", "", text)
    text = re.sub(r"\s+(?=[，。；：、）)])", "", text)
    return text.strip()


def extract_raw_page(page_number: int) -> str:
    """Use Poppler's reading order; PDF character cropping corrupts this source."""
    result = subprocess.run(
        [str(PDFTOTEXT), "-raw", "-f", str(page_number), "-l", str(page_number), str(SOURCE), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def clean_page(text: str) -> str:
    """Remove only recurring publisher furniture, retaining ordinary paragraph wraps."""
    kept = []
    for line in text.splitlines():
        line = normalise(line)
        if not line:
            kept.append("")
            continue
        if "中华内分泌代谢杂志" in line and "Vol." in line:
            continue
        if re.fullmatch(r"·\s*\d+\s*·", line):
            continue
        kept.append(line)
    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chinese_abstract(reader: PdfReader) -> tuple[str, str]:
    page_two = normalise(reader.pages[1].extract_text(extraction_mode="layout") or "")
    abstract = re.search(r"【提要】(.*?)【关键词】", page_two, re.S)
    keywords = re.search(r"【关键词】(.*?)(?:基金项目|DOI:|Guideline for)", page_two, re.S)
    if not abstract or not keywords:
        raise RuntimeError("Could not reliably locate the Chinese abstract and keywords.")
    return normalise(abstract.group(1)), normalise(keywords.group(1))


def markdown_table(title: str, headers: list[str], rows: list[list[str]], note: str = "") -> str:
    lines = [f"#### {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    if note:
        lines.extend(["", f"> 注：{note}"])
    return "\n".join(lines)


def replace_one(text: str, pattern: str, replacement: str, label: str) -> str:
    result, count = re.subn(pattern, replacement, text, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Expected one {label} block, found {count}.")
    return result


def optimise_tables(text: str) -> str:
    """Replace flattened PDF tables with searchable Markdown tables in place."""
    table1 = "\n\n".join(
        [
            "**检索摘要 - 中国成人 BMI 判定（2023）**：BMI <18.5 kg/m² 为偏瘦；18.5–23.9 kg/m² 为正常体重；24.0–27.9 kg/m² 为超重；BMI ≥28.0 kg/m² 为肥胖。",
            markdown_table(
                "表 1：国内外肥胖诊断标准",
                ["体重指数（kg/m²）", "中国标准（2023）", "世界卫生组织标准（2023）"],
                [
                    ["<18.5", "偏瘦", "体重不足"],
                    ["18.5–23.9", "正常体重", "正常范围"],
                    ["24.0–27.9", "超重", "超重"],
                    ["≥28.0（中国）", "肥胖", "≥30.0（肥胖）"],
                ],
            ),
        ]
    )
    tables23 = "\n\n".join(
        [
            markdown_table(
                "表 2：不同劳动强度及体型状态下的每日能量需求",
                ["劳动强度", "举例", "消瘦", "正常", "肥胖"],
                [
                    ["卧床休息", "-", "20–25", "15–20", "15"],
                    ["轻体力劳动", "办公室职员、教师或与其相当的活动量", "35", "30", "20–25"],
                    ["中体力劳动", "学生、司机、外科医生或与其相当的活动量", "40", "35", "30"],
                    ["重体力劳动", "建筑工、搬运工、冶炼工或与其相当的活动量", "45", "40", "35"],
                ],
                "每日热量需求单位为 kcal/kg 理想体重。",
            ),
            markdown_table(
                "表 3：宏量营养素配比",
                ["膳食模式", "碳水化合物", "蛋白质", "脂肪", "适用人群"],
                [
                    ["限能量平衡膳食", "55%–60%", "15%–20%", "25%–30%", "普通肥胖人群"],
                    ["低碳水化合物饮食", "20%–40%", "20%–30%", "30%–50%", "胰岛素抵抗、糖尿病前期患者"],
                    ["高蛋白饮食", "30%–40%", "25%–35%", "20%–30%", "需保留肌肉的减重者（如老年人）"],
                ],
            ),
        ]
    )
    tables456 = "\n\n".join(
        [
            "\n\n".join(
                [
                    "**检索摘要 - 超重人群运动方案（BMI 24.0–27.9 kg/m²）**：目标为减重、提高代谢；推荐每周 200–300 min 中等强度有氧运动（如椭圆机、游泳），并可每周 1–2 次高强度间歇训练（如快步抬膝 30 s 与原地踏步 60 s 交替）。",
                    markdown_table(
                        "表4：超重人群（BMI 24.0–27.9）运动安排",
                        ["人群分类", "体重指数（kg/m²）", "运动目标", "推荐运动类型与强度"],
                        [
                            ["消瘦人群（套餐 A）", "<18.5", "增肌、改善体质、管理/预防慢性病的发生", "抗阻训练：每周 3–4 次，8–12 次/组，中等重量（如深蹲、卧推）<br>有氧运动：中等强度（如慢跑、游泳），每周 2–3 次，30 min/次"],
                            ["正常体重（套餐 B）", "18.5–23.9", "维持体重、增强健康", "力量训练：全身肌群，每周 2 天（如哑铃、弹力带）<br>有氧运动：每周 150 min 中等强度（如慢跑、骑行）"],
                            ["超重人群（套餐 C）", "24.0–27.9", "减重、提高代谢", "有氧运动：每周 200–300 min 中等强度（如椭圆机、游泳）<br>高强度间歇训练：每周 1–2 次（如快步抬膝 30 s + 原地踏步 60 s 交替）"],
                            ["肥胖人群（套餐 D）", "≥28", "减重、改善关节功能", "低冲击有氧：水中有氧、固定自行车，每周 5–6 次，每次 45–60 min，累计 300 min/周以上<br>抗阻训练：自重训练（如靠墙深蹲、弹力带），每周 2–3 次；全身大肌群、每部位 2 组×10–12 次，含臀部、腿部、胸背与肩膀"],
                        ],
                    ),
                ]
            ),
            markdown_table(
                "表 5：基于年龄分层的肥胖人群运动建议",
                ["人群分类", "年龄层", "运动建议"],
                [
                    ["青少年", "10–17 岁", "每日≥60 min 中等至高强度活动<br>每周至少 3 次肌力与骨骼强化活动（如跳绳、体重抗阻、自行车）<br>应避免每日久坐超过 2 h"],
                    ["成人", "18–64 岁", "每周 150–300 min 中强度有氧运动（如快走、骑车、游泳）<br>每周至少 2 次抗阻训练（如自由重量、弹力带训练）<br>可选用高强度间歇训练增加效率"],
                    ["老年人", "≥65 岁", "推荐多模式运动组合（有氧 + 抗阻 + 平衡 + 柔软性训练），如太极、瑜伽、弹力带、固定脚踏车等<br>每周 3–5 次，强调安全与跌倒预防"],
                ],
            ),
            markdown_table(
                "表 6：常见慢性疾病人群运动建议",
                ["疾病类型", "运动建议类型与内容"],
                [
                    ["2 型糖尿病", "有氧运动：每周≥150 min 中等强度（如快走、游泳），避免连续 2 天不运动<br>抗阻训练：每周 2–3 次，提升胰岛素敏感性与肌力<br>运动前后需监测血糖，避免空腹运动，建议饭后 1–2 h 进行"],
                    ["高血压", "有氧运动：每周≥150 min（如快走、游泳、骑车）<br>抗阻训练：低负荷高次数，每周 2 次（如弹力带训练）<br>避免屏气用力、过度激烈运动，保持呼吸顺畅"],
                    ["骨关节炎", "有氧运动：选择低冲击类型（如水中有氧、固定脚踏车）每周 3–5 次<br>抗阻训练：重点强化下肢肌群（如股四头肌），使用自重或弹力带，每周 2–3 次<br>加强柔软性和平衡训练（如伸展、太极），避免关节疼痛明显时运动"],
                ],
            ),
        ]
    )
    table7 = markdown_table(
        "表 7：常用药物分类与作用机制",
        ["药物类别", "代表药物", "作用机制", "减重效果", "适应证", "用法用量"],
        [
            ["GLP-1 受体激动剂", "司美格鲁肽、利拉鲁肽", "激活 GLP-1 受体，延缓胃排空、增加饱腹感、调节中枢食欲", "4.7%–8.5%[32–33]", "司美格鲁肽（周制剂）：BMI≥27 kg/m² 合并糖尿病，或 BMI≥30 kg/m²<br>利拉鲁肽（日制剂）：BMI≥27 kg/m² 合并至少一种并发症", "司美格鲁肽：起始 0.25 mg/周，逐步增至 2.4 mg/周<br>利拉鲁肽：起始 0.6 mg/d，增至 3.0 mg/d"],
            ["基于 GLP-1 双靶点激动剂", "替尔泊肽", "同时激活 GLP-1 和 GIP 受体，协同抑制食欲、促进能量消耗", "11.3%–15.1%[34]", "BMI≥30 kg/m²，或 BMI≥27 kg/m² 合并并发症", "每周 1 次皮下注射 2.5 mg，持续 4 周；4 周后增加至 5 mg，每周 1 次；最大剂量 15 mg，每周 1 次"],
            ["脂肪酶抑制剂", "奥利司他", "抑制胃肠道脂肪酶，减少 30% 膳食脂肪吸收", "3.1%[33]", "高脂饮食习惯难以改变者", "在用餐中或者饭后 1 h 内服用，120 mg，tid"],
            ["二甲双胍", "二甲双胍", "改善胰岛素抵抗，减少肝糖输出，间接辅助减重（尤其适用于糖尿病前期/糖尿病患者）", "2.0%–4.0%", "主要适用于单纯饮食控制或者经体育锻炼控制血糖无效果的成年 2 型糖尿病患者", "起始剂量为 0.5 g，bid，或者 0.85 g，qd；随餐服用，可每周增加 0.5 g 或每 2 周增加 0.85 g；成人最大推荐剂量为每日 2.55 g"],
        ],
        "GLP-1：胰升糖素样肽-1；GIP：葡萄糖依赖性促胰岛素多肽。",
    )

    text = replace_one(text, r"表1 国内外肥胖诊断标准\n.*?(?=\n\(二\) 体型特征指标)", table1 + "\n", "表 1")
    text = replace_one(text, r"表2 不同劳动强度及体型状态下的每日能量需求\n.*?(?=\n\n<!-- 原文第 10 页 -->)", tables23, "表 2–3")
    text = replace_one(text, r"表4 基于体重指数分层运动建议\n.*?(?=\n\n<!-- 原文第 12 页 -->)", tables456, "表 4–6")
    text = replace_one(text, r"表7 常用药物分类与作用机制\n.*?(?=\n\n<!-- 原文第 13 页 -->)", table7, "表 7")
    return text


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)

    reader = PdfReader(str(SOURCE))
    abstract, keywords = chinese_abstract(reader)
    parts = [
        "# 中国成人体重管理指南",
        "",
        "> Dify 知识库清洗版。保留中文摘要与正文；已排除作者与单位、英文重复内容、"
        "期刊页眉页脚、页码、作者声明及文末引文。",
        "",
        "- 来源：中华内分泌代谢杂志，2025 年 11 月，第 41 卷第 11 期",
        "- DOI：10.3760/cma.j.cn311282-20250526-00280",
        "- 清洗范围：原文第 2 页摘要，以及第 5-16 页正文；第 16 页仅保留引文前的正文。",
        "",
        "## 摘要",
        "",
        abstract,
        "",
        f"**关键词：** {keywords}",
        "",
        "## 正文",
    ]

    for page_number in range(5, 17):
        page_text = clean_page(extract_raw_page(page_number))
        if page_number == 16:
            # The final page continues the lifestyle section before bibliography.
            page_text = re.split(r"利益冲突|参考文献", page_text, maxsplit=1)[0].strip()
        if page_text:
            parts.extend(["", f"<!-- 原文第 {page_number} 页 -->", "", page_text])

    text = optimise_tables("\n".join(parts).rstrip()) + "\n"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8")
    required = ("七、体重管理的医学营养", "#### 表 1", "#### 表 2", "#### 表 3", "#### 表4", "#### 表 5", "#### 表 6", "#### 表 7", "九、体重管理的药物治疗")
    forbidden = ("ꎬ", "ꎮ", "ꎻ", "̄", "中华内分泌代谢杂志 2025 年")
    missing = [item for item in required if item not in text]
    present = [item for item in forbidden if item in text]
    if missing or present or len(text) < 20000:
        raise RuntimeError(f"Validation failed: missing={missing}, forbidden={present}, chars={len(text)}")
    print(f"Wrote {OUTPUT}")
    print(f"Characters: {len(text)}")


if __name__ == "__main__":
    main()
