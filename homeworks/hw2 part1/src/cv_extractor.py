# src/cv_extractor.py
import json
from langchain_core.messages import HumanMessage, SystemMessage
from src.schemas import CVProfile

CV_EXTRACTION_PROMPT = """
You are an information extraction engine.
Extract a resume/CV into STRICT JSON.

Rules:
- Output valid JSON only (no markdown).
- If uncertain, keep the field null instead of guessing.
- Normalize skills into a list of short strings.
- Preserve dates as seen (e.g., "2020", "May 2020", "Present").
- If text is messy due to PDF parsing, infer cautiously.

Required JSON keys:
full_name, headline, current_location, phone, email, skills, experiences, education, raw_text_excerpt

experiences[] keys:
company, title, start_date, end_date, location, description

education[] keys:
school, degree, field_of_study, graduation_year, start_year, end_year
"""

def extract_cv_structured(llm, clean_text: str) -> CVProfile:
    messages = [
        SystemMessage(content=CV_EXTRACTION_PROMPT),
        HumanMessage(content=f"CV text:\n\n{clean_text[:12000]}")  # 控制长度
    ]
    resp = llm.invoke(messages)
    content = resp.content if isinstance(resp.content, str) else str(resp.content)

    # 兼容模型偶尔输出 ```json ... ```
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content.replace("json", "", 1).strip()

    data = json.loads(content)
    # 可选：存一个片段方便报告引用
    data["raw_text_excerpt"] = clean_text[:1000]
    return CVProfile.model_validate(data)