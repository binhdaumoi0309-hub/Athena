"""Optional, tightly scoped Playwright MCP connection for Google ADK."""

import os

from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters


def playwright_mcp_enabled() -> bool:
    """Return whether live browser tools were explicitly enabled."""
    return os.getenv("ENABLE_PLAYWRIGHT_MCP", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def create_playwright_mcp_toolset() -> McpToolset:
    """Create the official Playwright MCP toolset in isolated, headless mode.

    The browser is origin-limited. File downloads are handled by the ingestion
    downloader, so the chat agent does not receive unrestricted filesystem access.
    """
    command = os.getenv("PLAYWRIGHT_MCP_COMMAND", "npx").strip() or "npx"
    package = os.getenv("PLAYWRIGHT_MCP_PACKAGE", "@playwright/mcp@latest").strip()
    connection_timeout = float(os.getenv("PLAYWRIGHT_MCP_CONNECTION_TIMEOUT", "60"))
    action_timeout = os.getenv("PLAYWRIGHT_MCP_ACTION_TIMEOUT_MS", "15000")
    navigation_timeout = os.getenv("PLAYWRIGHT_MCP_NAVIGATION_TIMEOUT_MS", "90000")
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=command,
                args=[
                    "-y",
                    package,
                    "--headless",
                    "--isolated",
                    "--browser",
                    "chromium",
                    "--timeout-action",
                    action_timeout,
                    "--timeout-navigation",
                    navigation_timeout,
                    "--block-service-workers",
                    "--allowed-origins",
                    "https://benhvientimhanoi.vn;https://www.benhvientimhanoi.vn;"
                    "https://drive.google.com;https://drive.usercontent.google.com",
                ],
            ),
            timeout=connection_timeout,
        ),
        tool_filter=[
            "browser_navigate",
            "browser_snapshot",
            "browser_click",
            "browser_wait_for",
        ],
        tool_name_prefix="hospital_web",
    )
