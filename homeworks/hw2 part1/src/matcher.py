# src/matcher.py
import json
from langchain_core.messages import HumanMessage, SystemMessage
from src.schemas import CVProfile, SocialCandidate

SEARCH_PROMPT = """
You are a CV verification agent.
Use ONLY the available MCP social tools to find the best matching LinkedIn and Facebook profiles.

Goal:
- Find likely LinkedIn and Facebook profiles for the CV person
- Prefer high precision over recall
- Use name + location + company + education hints from CV
- If ambiguous, keep multiple candidates with scores and reasons
- Do NOT fabricate profile IDs

Final output must be STRICT JSON:
{
  "linkedin_candidates": [
    {"platform":"linkedin","candidate_id":"...","display_name":"...","profile_url":"...","score":0.0,"reason":"..."}
  ],
  "facebook_candidates": [
    {"platform":"facebook","candidate_id":"...","display_name":"...","profile_url":"...","score":0.0,"reason":"..."}
  ]
}
"""

async def search_social_candidates(llm_with_tools, tools, cv: CVProfile):
    hints = {
        "full_name": cv.full_name,
        "location": cv.current_location,
        "skills": cv.skills[:8],
        "education": [e.model_dump() for e in cv.education[:3]],
        "experiences": [x.model_dump() for x in cv.experiences[:5]],
    }
    user_prompt = f"""
Find the best matching social profiles for this CV person.

CV hints JSON:
{json.dumps(hints, ensure_ascii=False)}
"""
    from src.utils import run_tool_agent
    final_msg, _ = await run_tool_agent(llm_with_tools, tools, SEARCH_PROMPT, user_prompt, max_steps=8)

    content = final_msg.content if isinstance(final_msg.content, str) else str(final_msg.content)
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`").replace("json", "", 1).strip()
    data = json.loads(content)
    print(f"Search candidates for {cv.full_name}: {data}")
    linkedin = [SocialCandidate.model_validate(x) for x in data.get("linkedin_candidates", [])]
    facebook = [SocialCandidate.model_validate(x) for x in data.get("facebook_candidates", [])]
    return linkedin, facebook