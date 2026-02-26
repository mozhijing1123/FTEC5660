# src/utils.py
import json
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

def _safe_str(obj, max_len=8000):
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        s = str(obj)
    return s[:max_len]

async def run_tool_agent(llm_with_tools, tools, system_prompt: str, user_prompt: str, max_steps: int = 8):
    tool_map = {t.name: t for t in tools}
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    for step in range(max_steps):
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        tool_calls = getattr(ai_msg, "tool_calls", None) or []
        if not tool_calls:
            return ai_msg, messages  # 最终答案

        for tc in tool_calls:
            name = tc["name"]
            args = tc.get("args", {})
            tool = tool_map[name]

            try:
                # MCP工具/本地工具尽量用异步
                if hasattr(tool, "ainvoke"):
                    tool_result = await tool.ainvoke(args)
                else:
                    tool_result = tool.invoke(args)
            except Exception as e:
                tool_result = {"error": str(e), "tool": name, "args": args}

            messages.append(
                ToolMessage(
                    content=_safe_str(tool_result),
                    tool_call_id=tc["id"]
                )
            )

    return ai_msg, messages