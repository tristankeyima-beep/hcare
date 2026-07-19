"""Build Dify-ready Markdown volumes from the 2024 adult-obesity food guide.

The source is a 70-page, single-column government PDF.  It is deliberately
split by the guide's own appendix boundaries so that the large regional-menu
section does not dilute retrieval of general dietary principles.
"""

from __future__ import annotations

import os
import re
import subprocess
import unicodedata
from pathlib import Path


SPECIAL_DIR = Path(__file__).resolve().parents[1]
SOURCE = SPECIAL_DIR / "01_知识库文档/成人肥胖食养指南_2024原始PDF.pdf"
OUTPUT_DIR = SPECIAL_DIR / "01_知识库文档"
PDFTOTEXT = Path(
    os.environ.get(
        "PDFTOTEXT_PATH",
        "/Users/Tristan/.cache/codex-runtimes/codex-primary-runtime/"
        "dependencies/native/poppler/poppler/bin/pdftotext",
    )
)

FORMAL_PREFIX = "成人肥胖食养指南（国家卫生健康委办公厅，2024年版）"
VOLUMES = (
    ("核心原则与食物选择", range(3, 22), ("一、前言", "附录 2")),
    ("不同地区食谱示例", range(22, 63), ("附录 3", "东北地区")),
    ("食养方、判定标准与活动强度", range(63, 71), ("附录 4", "附录 6")),
)


def clean_page(text: str) -> str:
    """Remove standalone printed page numbers while preserving tables and lines."""
    text = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    lines = []
    for line in text.splitlines():
        line = line.rstrip()
        if re.fullmatch(r"\s*\d{1,3}\s*", line):
            continue
        lines.append(line)
    cleaned = "\n".join(lines).strip()
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def build_documents(pages: dict[int, str]) -> list[dict[str, str]]:
    """Create the three user-visible, Dify-ready Markdown volumes."""
    documents = []
    for subtitle, page_range, expected_markers in VOLUMES:
        blocks = []
        for pdf_page in page_range:
            raw = pages.get(pdf_page, "")
            cleaned = clean_page(raw)
            if cleaned:
                printed_page = pdf_page - 2
                blocks.append(f"<!-- 原文第 {printed_page} 页 -->\n\n{cleaned}")
        title = f"{FORMAL_PREFIX}·{subtitle}"
        content = (
            f"# {title}\n\n"
            "> 来源：国家卫生健康委办公厅发布《成人肥胖食养指南（2024年版）》。"
            "本分册仅按原文结构拆分，未改变原文建议、食谱或数值。\n\n"
            "> 适用提示：本指南主要面向基层卫生工作者、营养指导人员以及无合并症或并发症的成人肥胖患者；"
            "合并疾病或特殊人群应在医生或营养专业人员指导下使用。\n\n"
            "---\n\n"
            + "\n\n".join(blocks)
            + "\n"
        )
        missing = [marker for marker in expected_markers if marker not in content]
        if missing:
            raise ValueError(f"{subtitle} missing expected markers: {missing}")
        documents.append({"title": title, "content": content})
    return documents


def extract_pages(pdf_path: Path) -> dict[int, str]:
    if not PDFTOTEXT.exists():
        raise FileNotFoundError(f"pdftotext not found: {PDFTOTEXT}")
    result = subprocess.run(
        [str(PDFTOTEXT), "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return {index: page for index, page in enumerate(result.stdout.split("\f"), start=1)}


def output_path(title: str) -> Path:
    return OUTPUT_DIR / f"{title}.md"


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source PDF not found: {SOURCE}")
    pages = extract_pages(SOURCE)
    documents = build_documents(pages)
    for document in documents:
        path = output_path(document["title"])
        path.write_text(document["content"], encoding="utf-8")
        print(f"Wrote {path} ({len(document['content'])} characters)")


if __name__ == "__main__":
    main()
