# src/reporter.py
import json
from langchain_core.messages import HumanMessage, SystemMessage
from src.schemas import VerificationResult, CVProfile, Discrepancy

SUMMARY_PROMPT = """
You are a CV verification analyst.
Given CV structured data and 我们在网上可能的检索 findings, produce:
1) overall_status: verified / partially_verified / suspicious / unable_to_verify
2) score: 0~1     （越可疑分数越高反之分数越低 verified (<0.25)/ partially_verified (<0.6) / suspicious (<0.8)/ unable_to_verify (<1) )
3) concise summary (3-6 sentences) 

由于查询到的社交资料往往不完整，且CV本身可能存在模糊或夸大，可以适当宽容一些， 但如果什么都找不到或有巨大矛盾需要谨慎。
Output STRICT JSON only:
{"overall_status":"...","score":0.0,"summary":"..."}
"""

def summarize_verification(llm, cv: CVProfile, discrepancies: list[Discrepancy], web_search_results):
    payload = {
        "cv": cv.model_dump(),
        # "discrepancies": [d.model_dump() for d in discrepancies],
    }
    resp = llm.invoke([
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content=json.dumps(payload, ensure_ascii=False)[:15000]),
        HumanMessage(content=str(web_search_results)[:15000])
    ])
    txt = resp.content if isinstance(resp.content, str) else str(resp.content)
    txt = txt.strip()
    if txt.startswith("```"):
        txt = txt.strip("`").replace("json", "", 1).strip()
    return json.loads(txt)

def render_markdown_report(result: VerificationResult) -> str:
    lines = []
    lines.append(f"# CV Verification Report - {result.file}")
    lines.append("")
    lines.append(f"**Person:** {result.person_name}")
    lines.append(f"**Overall Status:** {result.overall_status}")
    lines.append(f"**Confidence:** {result.confidence:.2f}")
    lines.append("")
    lines.append("## Selected Profiles")
    lines.append(f"- LinkedIn: {result.selected_linkedin}")
    lines.append(f"- Facebook: {result.selected_facebook}")
    lines.append("")
    lines.append("## Summary")
    lines.append(result.summary)
    lines.append("")
    lines.append("## Discrepancies")
    for d in result.discrepancies:
        lines.append(f"- **{d.field}** | {d.status} | severity={d.severity}")
        lines.append(f"  - CV: {d.cv_value}")
        lines.append(f"  - Social: {d.social_value}")
        if d.evidence:
            lines.append(f"  - Evidence: {d.evidence}")
        if d.rationale:
            lines.append(f"  - Rationale: {d.rationale}")
    return "\n".join(lines)