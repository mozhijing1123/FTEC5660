# src/mcp_client.py
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import tool

@tool
def say_hello(name: str) -> str:
    """Say hello to a person by name."""
    return f"Hello, {name}! 👋"

async def load_tools():
    client = MultiServerMCPClient({
        "social_graph": {
            "transport": "http",
            "url": "https://ftec5660.ngrok.app/mcp",
            "headers": {"ngrok-skip-browser-warning": "true"}
        }
    })
    mcp_tools = await client.get_tools()
    # tools = mcp_tools + [say_hello]
    tools = mcp_tools
    return client, tools