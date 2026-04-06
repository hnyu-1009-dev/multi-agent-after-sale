import asyncio
from typing import Any

from app.config.settings import settings
from app.infrastructure.logging.logger import logger
from app.infrastructure.tools.mcp.mcp_servers import all_mcp_clients


async def _connect_client(client: Any) -> None:
    timeout = max(1, settings.MCP_CONNECT_TIMEOUT_SECONDS)
    client_name = getattr(client, "name", client.__class__.__name__)
    try:
        await asyncio.wait_for(client.connect(), timeout=timeout)
        logger.info(f"MCP client connected: {client_name}")
    except asyncio.TimeoutError:
        logger.warning(f"MCP client connect timed out after {timeout}s: {client_name}")
    except Exception as exc:
        logger.warning(f"MCP client connect failed: {client_name}: {exc}")


async def mcp_connect() -> None:
    if not settings.MCP_STARTUP_ENABLED:
        logger.info("MCP startup connect is disabled by configuration.")
        return
    if not all_mcp_clients:
        logger.info("No MCP clients are configured. Skipping startup connect.")
        return

    await asyncio.gather(*(_connect_client(client) for client in all_mcp_clients))


async def _cleanup_client(client: Any) -> None:
    client_name = getattr(client, "name", client.__class__.__name__)
    try:
        await client.cleanup()
        logger.info(f"MCP client cleaned up: {client_name}")
    except Exception as exc:
        logger.warning(f"MCP client cleanup failed: {client_name}: {exc}")


async def mcp_cleanup() -> None:
    if not all_mcp_clients:
        return
    await asyncio.gather(*(_cleanup_client(client) for client in all_mcp_clients))
