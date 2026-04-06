import logging
from typing import Any, Dict, List, Optional

from agents.mcp import MCPServerSse, MCPServerStreamableHttp

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _has_value(value: Optional[str]) -> bool:
    return bool(value and value.strip())


def _create_search_mcp_client() -> Optional[MCPServerStreamableHttp]:
    if not _has_value(settings.DASHSCOPE_BASE_URL):
        logger.warning("DashScope MCP is disabled: DASHSCOPE_BASE_URL is empty.")
        return None
    if not _has_value(settings.AL_BAILIAN_API_KEY):
        logger.warning("DashScope MCP is disabled: AL_BAILIAN_API_KEY is empty.")
        return None

    params: Dict[str, Any] = {
        "url": settings.DASHSCOPE_BASE_URL,
        "headers": {"Authorization": f"Bearer {settings.AL_BAILIAN_API_KEY}"},
        "timeout": settings.MCP_CONNECT_TIMEOUT_SECONDS,
        "sse_read_timeout": settings.MCP_CONNECT_TIMEOUT_SECONDS * 30,
    }
    return MCPServerStreamableHttp(
        name="通用联网搜索",
        params=params,
        client_session_timeout_seconds=settings.MCP_CONNECT_TIMEOUT_SECONDS * 10,
        cache_tools_list=True,
    )


def _create_baidu_mcp_client() -> Optional[MCPServerSse]:
    if not _has_value(settings.BAIDUMAP_AK):
        logger.warning("Baidu Map MCP is disabled: BAIDUMAP_AK is empty.")
        return None

    params: Dict[str, Any] = {
        "url": f"https://mcp.map.baidu.com/sse?ak={settings.BAIDUMAP_AK}",
        "timeout": settings.MCP_CONNECT_TIMEOUT_SECONDS,
        "sse_read_timeout": settings.MCP_CONNECT_TIMEOUT_SECONDS * 30,
    }
    return MCPServerSse(
        name="百度地图",
        params=params,
        client_session_timeout_seconds=settings.MCP_CONNECT_TIMEOUT_SECONDS * 10,
        cache_tools_list=True,
    )


search_mcp_client = _create_search_mcp_client()
baidu_mcp_client = _create_baidu_mcp_client()

search_mcp_servers: List[Any] = [search_mcp_client] if search_mcp_client else []
baidu_mcp_servers: List[Any] = [baidu_mcp_client] if baidu_mcp_client else []
all_mcp_clients: List[Any] = [
    client for client in (baidu_mcp_client, search_mcp_client) if client is not None
]
