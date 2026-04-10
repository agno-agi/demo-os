"""Exa MCP integration helpers."""

from os import getenv

from agno.tools.mcp import MCPTools


def get_exa_mcp_tools(tools: str = "web_search_exa") -> list:
    """Return MCPTools for Exa. Authenticated if EXA_API_KEY is set, free tier otherwise."""
    key = getenv("EXA_API_KEY", "")
    if key:
        url = f"https://mcp.exa.ai/mcp?exaApiKey={key}&tools={tools}"
    else:
        url = f"https://mcp.exa.ai/mcp?tools={tools}"
    return [MCPTools(url=url)]
