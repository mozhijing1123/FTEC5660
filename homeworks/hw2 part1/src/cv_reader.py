# src/cv_reader.py
import os
import re
from markitdown import MarkItDown

def clean_cv_text(text: str) -> str:
    # 去掉一些 PDF 乱码
    text = re.sub(r"\(cid:\d+\)", " ", text)
    # 去掉多余竖线（表格转markdown导致）
    text = re.sub(r"\|", " ", text)
    # 去掉重复分隔线
    text = re.sub(r"-{3,}", " ", text)
    # 合并多空格
    text = re.sub(r"[ \t]+", " ", text)
    # 合并多空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def load_all_cvs(cv_dir="downloaded_cvs"):
    md = MarkItDown(enable_plugins=False)

    pdf_files = sorted(
        [f for f in os.listdir(cv_dir) if f.lower().endswith(".pdf")],
        key=lambda x: int("".join(filter(str.isdigit, x)) or 0)
    )

    all_cvs = []
    for pdf_name in pdf_files:
        pdf_path = os.path.join(cv_dir, pdf_name)
        result = md.convert(pdf_path)
        raw_text = result.text_content or ""
        all_cvs.append({
            "file": pdf_name,
            "raw_text": raw_text,
            "clean_text": clean_cv_text(raw_text)
        })
    return all_cvs