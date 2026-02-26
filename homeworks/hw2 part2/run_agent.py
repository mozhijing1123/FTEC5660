import os
import re
import json
import time
import requests
from typing import Any, Optional
from datetime import datetime, UTC

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    MOLTBOOK_API_KEY,
    MOLTBOOK_BASE_URL,
)

# -------------------------
# 1) 配置
# -------------------------

TARGET_SUBMOLT = "ftec5660"
TARGET_POST_URL = "https://www.moltbook.com/post/47ff50f3-8255-4dee-87f4-2c3637c7351c"
TARGET_POST_ID = "47ff50f3-8255-4dee-87f4-2c3637c7351c"

HEADERS = {
    "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
    "Content-Type": "application/json",
}

# -------------------------
# 2) LLM
# -------------------------
llm = ChatOpenAI(
    model=OPENAI_MODEL,
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    temperature=0,
)

# -------------------------
# 3) 日志工具
# -------------------------
def log(section: str, message: str):
    ts = datetime.now(UTC).strftime("%H:%M:%S")
    print(f"[{ts}] [{section}] {message}")

def pretty(obj: Any, max_len: int = 1200):
    try:
        text = json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    except Exception:
        text = str(obj)
    return text if len(text) <= max_len else text[:max_len] + "\n...<truncated>"

def _safe_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return {"raw_text": resp.text}

def _api_request(
    method: str,
    path: str,
    *,
    params: Optional[dict] = None,
    body: Optional[dict] = None,
    timeout: int = 20,
    retries: int = 2,
) -> dict:
    """
    通用 Moltbook API 调用器，统一处理错误/限流/日志。
    """
    if not MOLTBOOK_API_KEY:
        return {"ok": False, "error": "MOLTBOOK_API_KEY is empty"}

    url = f"{MOLTBOOK_BASE_URL}{path}"
    last_err = None

    for attempt in range(retries + 1):
        try:
            resp = requests.request(
                method=method.upper(),
                url=url,
                headers=HEADERS,
                params=params,
                json=body,
                timeout=timeout,
            )
            data = _safe_json(resp)

            result = {
                "ok": resp.ok,
                "status_code": resp.status_code,
                "path": path,
                "method": method.upper(),
                "params": params,
                "body": body,
                "data": data,
                "rate_limit": {
                    "limit": resp.headers.get("X-RateLimit-Limit"),
                    "remaining": resp.headers.get("X-RateLimit-Remaining"),
                    "reset": resp.headers.get("X-RateLimit-Reset"),
                },
            }

            # 简单重试：429 / 5xx
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                sleep_s = 1.5 * (attempt + 1)
                log("RETRY", f"{method.upper()} {path} -> {resp.status_code}, sleep {sleep_s}s")
                time.sleep(sleep_s)
                continue

            return result

        except requests.RequestException as e:
            last_err = str(e)
            if attempt < retries:
                sleep_s = 1.5 * (attempt + 1)
                log("RETRY", f"{method.upper()} {path} request error: {e}, sleep {sleep_s}s")
                time.sleep(sleep_s)
            else:
                break

    return {
        "ok": False,
        "error": f"Request failed after retries: {last_err}",
        "method": method.upper(),
        "path": path,
    }

def extract_post_id(url_or_id: str) -> str:
    """
    支持直接传 UUID 或 Moltbook 帖子 URL。
    """
    m = re.search(r"/post/([0-9a-fA-F-]{36})", url_or_id)
    if m:
        return m.group(1)
    return url_or_id.strip()

# -------------------------
# 4) 工具定义（LangChain tools）
# -------------------------

@tool
def get_agent_me() -> dict:
    """Get current agent profile to verify authentication."""
    return _api_request("GET", "/agents/me")

@tool
def get_agent_status() -> dict:
    """Check claim/verification status of the current agent."""
    return _api_request("GET", "/agents/status")

@tool
def get_feed(sort: str = "hot", limit: int = 10) -> dict:
    """Get Moltbook global posts feed. sort: hot/new/top/rising."""
    limit = max(1, min(int(limit), 25))
    return _api_request("GET", "/posts", params={"sort": sort, "limit": limit})

@tool
def search_moltbook(query: str, limit: int = 10) -> dict:
    """Search posts, agents, and submolts."""
    limit = max(1, min(int(limit), 25))
    return _api_request("GET", "/search", params={"q": query, "limit": limit})

@tool
def get_post(post_id: str) -> dict:
    """Get a single post by ID (UUID) or Moltbook post URL."""
    pid = extract_post_id(post_id)
    return _api_request("GET", f"/posts/{pid}")

@tool
def get_post_comments(post_id: str, sort: str = "top") -> dict:
    """Get comments of a post. sort: top/new/controversial."""
    pid = extract_post_id(post_id)
    return _api_request("GET", f"/posts/{pid}/comments", params={"sort": sort})

@tool
def subscribe_submolt(name: str) -> dict:
    """Subscribe to a submolt by name, e.g. 'ftec5660'."""
    name = name.strip().lstrip("/").replace("m/", "")
    return _api_request("POST", f"/submolts/{name}/subscribe")

@tool
def create_post(submolt: str, title: str, content: Optional[str] = None, url: Optional[str] = None) -> dict:
    """Create a text or link post. Provide content OR url."""
    submolt = submolt.strip().lstrip("/").replace("m/", "")
    payload = {"submolt": submolt, "title": title}
    if content:
        payload["content"] = content
    if url:
        payload["url"] = url
    return _api_request("POST", "/posts", body=payload)

@tool
def comment_post(post_id: str, content: str, parent_id: Optional[str] = None) -> dict:
    """Add a comment to a post. Optionally reply to an existing comment with parent_id."""
    pid = extract_post_id(post_id)
    payload = {"content": content}
    if parent_id:
        payload["parent_id"] = parent_id
    return _api_request("POST", f"/posts/{pid}/comments", body=payload)

@tool
def upvote_post(post_id: str) -> dict:
    """Upvote a post by ID (UUID) or Moltbook post URL."""
    pid = extract_post_id(post_id)
    return _api_request("POST", f"/posts/{pid}/upvote")

# -------------------------
# 5) 系统提示词
# -------------------------
SYSTEM_PROMPT = f"""
You are a Moltbook AI agent executing a homework task.

Primary objective (must complete exactly these tasks):
1) Authenticate by checking current agent profile
2) Subscribe to /m/{TARGET_SUBMOLT}
3) Upvote and comment on the target post: {TARGET_POST_URL}

Rules:
- Be precise. Do NOT do extra unrelated actions.
- Prefer idempotent behavior: check existing state/comments before commenting if possible.
- Never spam or repeat the same comment.
- If a tool returns an error because an action already happened (e.g., already subscribed/upvoted), treat that as acceptable and continue.
- Keep comment short, professional, and relevant to the target post.
- End with a concise completion summary listing the tool calls made and outcomes.

Available tools:
- get_agent_me
- get_agent_status
- get_feed
- search_moltbook
- get_post
- get_post_comments
- subscribe_submolt
- create_post
- comment_post
- upvote_post
"""

# -------------------------
# 6) Agent Loop（
# -------------------------
def moltbook_agent_loop(
    instruction: Optional[str] = None,
    max_turns: int = 10,
    verbose: bool = True,
):
    log("INIT", "Starting Moltbook agent loop")

    tools = [
        get_agent_me,
        get_agent_status,
        get_feed,
        search_moltbook,
        get_post,
        get_post_comments,
        subscribe_submolt,
        create_post,
        comment_post,
        upvote_post,
    ]

    agent = llm.bind_tools(tools)

    history = [("system", SYSTEM_PROMPT)]

    if instruction:
        history.append(("human", f"Human instruction: {instruction}"))
        log("HUMAN", instruction)
    else:
        history.append(("human", "Perform the homework task now."))
        log("HUMAN", "No custom instruction – homework mode")

    for turn in range(1, max_turns + 1):
        log("TURN", f"Turn {turn}/{max_turns} started")
        turn_start = time.time()

        response = agent.invoke(history)
        history.append(response)

        if verbose:
            content_text = response.content
            if isinstance(content_text, list):
                content_text = str(content_text)
            log("LLM", "Model responded")
            log("LLM.CONTENT", content_text or "<empty>")
            log("LLM.TOOL_CALLS", pretty(response.tool_calls or []))

        if not getattr(response, "tool_calls", None):
            elapsed = round(time.time() - turn_start, 2)
            log("STOP", f"No tool calls — final answer produced in {elapsed}s")
            return response.content

        for i, call in enumerate(response.tool_calls, start=1):
            tool_name = call["name"]
            args = call.get("args", {})
            tool_id = call["id"]

            log("TOOL", f"[{i}] Calling `{tool_name}`")
            log("TOOL.ARGS", pretty(args))

            tool_fn = globals().get(tool_name)
            tool_start = time.time()

            try:
                if tool_fn is None:
                    raise ValueError(f"Tool not found: {tool_name}")
                result = tool_fn.invoke(args)
                status = "success"
            except Exception as e:
                result = {"ok": False, "error": str(e), "tool": tool_name}
                status = "error"

            tool_elapsed = round(time.time() - tool_start, 2)
            log("TOOL.RESULT", f"{tool_name} finished ({status}) in {tool_elapsed}s")

            if verbose:
                log("TOOL.OUTPUT", pretty(result))

            history.append(
                ToolMessage(
                    tool_call_id=tool_id,
                    content=json.dumps(result, ensure_ascii=False, default=str),
                )
            )

        turn_elapsed = round(time.time() - turn_start, 2)
        log("TURN", f"Turn {turn} completed in {turn_elapsed}s")

    log("STOP", "Max turns reached without final answer")
    return "Agent stopped after reaching max turns."

# -------------------------
# 7) run
# -------------------------
def run_homework_part2(comment_text: Optional[str] = None, max_turns: int = 10):
    """
    用于作业提交的标准入口。建议保留日志输出截图到 report.pdf。
    """
    if not comment_text:
        comment_text = (
            "Interesting framing. One practical angle is to design agents with "
            "explicit tool constraints and idempotent checks before actions "
            "(e.g., verify state before voting/commenting) to reduce accidental spam."
        )

    instruction = f"""
Complete the homework task exactly:
- Authenticate using the API key (check current agent profile)
- Subscribe to /m/{TARGET_SUBMOLT}
- Upvote the post {TARGET_POST_URL}
- Comment on that post with this exact comment (unless I already commented the same thing):
{comment_text}

Before commenting, check post comments and avoid duplicate comments from this agent.
Do not create any new post. Do not perform unrelated searches.
Return a final summary of what succeeded/failed.
""".strip()

    return moltbook_agent_loop(
        instruction=instruction,
        max_turns=max_turns,
        verbose=True,
    )

if __name__ == "__main__":
    run_homework_part2()