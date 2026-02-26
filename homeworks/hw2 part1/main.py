# main.ipynb / main.py
import os
import json
import asyncio
from langchain_openai import ChatOpenAI

from src.cv_reader import load_all_cvs
from src.cv_extractor import extract_cv_structured
from src.mcp_client import load_tools
from src.matcher import search_social_candidates
from src.verifier import compare_basic
from src.reporter import summarize_verification, render_markdown_report
from src.schemas import VerificationResult


def evaluate(scores, groundtruth, threshold=0.5):
    """
    scores: list of floats in [0, 1], length = 5
    groundtruth: list of ints (0 or 1), length = 5
    """
    assert len(scores) == 5
    assert len(groundtruth) == 5

    correct = 0
    decisions = []

    for s, gt in zip(scores, groundtruth):
        pred = 1 if s > threshold else 0
        decisions.append(pred)
        if pred == gt:
            correct += 1

    final_score = correct / len(scores)

    return {
        "decisions": decisions,
        "correct": correct,
        "total": len(scores),
        "final_score": final_score
    }
    
    
async def fetch_full_profile(tool_list, platform: str, candidate_id: str):
    tool_map = {t.name: t for t in tool_list}

    if platform == "linkedin":
        tool_name = "get_linkedin_profile"
    elif platform == "facebook":
        tool_name = "get_facebook_profile"
    else:
        return None

    if tool_name not in tool_map:
        return None

    tool = tool_map[tool_name]
    try:
        if hasattr(tool, "ainvoke"):
            # 参数名可能依MCP定义不同（id / person_id / profile_id）
            # 你需要根据实际tool schema微调这里
            return await tool.ainvoke({"id": candidate_id})
        else:
            return tool.invoke({"id": candidate_id})
    except Exception as e:
        return {"error": str(e), "candidate_id": candidate_id, "platform": platform}

async def verify_one_cv(item, llm, llm_with_tools, tools, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)

    file_name = item["file"]
    clean_text = item["clean_text"]

    # 1) CV结构化
    cv = extract_cv_structured(llm, clean_text)
    with open(os.path.join(output_dir, file_name.replace(".pdf", "_structured.json")), "w", encoding="utf-8") as f:
        json.dump(cv.model_dump(), f, ensure_ascii=False, indent=2)

    # 2) 候选搜索
    linkedin_candidates, facebook_candidates = await search_social_candidates(llm_with_tools, tools, cv)

    # 3) 选前1个（可以做更复杂重排序）
    best_li = linkedin_candidates[0] if linkedin_candidates else None
    best_fb = facebook_candidates[0] if facebook_candidates else None

    # 4) 拉取完整资料
    li_profile = await fetch_full_profile(tools, "linkedin", best_li.candidate_id) if best_li else None
    fb_profile = await fetch_full_profile(tools, "facebook", best_fb.candidate_id) if best_fb else None
    
    # 5) 字段核验   
    discrepancies = compare_basic(cv, li_profile, fb_profile)

    web_search_results = {
        "inkedin_candidates": linkedin_candidates,
        "facebook_candidates": facebook_candidates,
        "best_linkedin": li_profile,
        "best_facebook": fb_profile
    }
    # 6) LLM总结最终判定
    summary_obj = summarize_verification(llm, cv, discrepancies, web_search_results)

    result = VerificationResult(
        file=file_name,
        person_name=cv.full_name,
        overall_status=summary_obj["overall_status"],
        confidence=float(summary_obj["score"]),
        selected_linkedin=best_li.model_dump() if best_li else None,
        selected_facebook=best_fb.model_dump() if best_fb else None,
        discrepancies=discrepancies,
        summary=summary_obj["summary"]
    )

    # 7) 输出 JSON + MD
    json_path = os.path.join(output_dir, file_name.replace(".pdf", "_verification.json"))
    md_path = os.path.join(output_dir, file_name.replace(".pdf", "_report.md"))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown_report(result))

    return result

async def main():
    # LLM
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-5.1"),  
        api_key=os.getenv("OPENAI_API_KEY", "sk-e2GpF64Q21z5Ha1qt3Eg6NJiiBJrhFuf5s4rhr6nH9M78OWR"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.chatanywhere.tech/v1"),
        temperature=0
    )

    # Tools
    client, tools = await load_tools()
    llm_with_tools = llm.bind_tools(tools)

    # CVs
    all_cvs = load_all_cvs("downloaded_cvs")

    all_results = []
    
    # all_cvs = all_cvs[3:5]
    
    for item in all_cvs:
        try:
            result = await verify_one_cv(item, llm, llm_with_tools, tools, output_dir="outputs")
            all_results.append(result)
            print(f"✅ Done: {item['file']} -> {result.overall_status} ({result.confidence:.2f})")
        except Exception as e:
            print(f"❌ Failed: {item['file']}: {e}")

    # 汇总文件
    summary = [
        {
            "file": r.file,
            "name": r.person_name,
            "status": r.overall_status,
            "confidence": r.confidence,
            "num_discrepancies": len(r.discrepancies)
        }
        for r in all_results
    ]

    with open("outputs/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    scores = [1-r.confidence for r in all_results]
    groundtruth = [1,1,1,0, 0]   # 你需要根据实际情况填写每个CV的真实标签
    eval_result = evaluate(scores, groundtruth, threshold=0.5)
    print(f"Evaluation: {eval_result}")

if __name__ == "__main__":
    asyncio.run(main())