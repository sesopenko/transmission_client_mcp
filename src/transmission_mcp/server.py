"""FastMCP server entrypoint for the Transmission MCP server.

Run with::

    uv run python -m transmission_mcp

or via the installed script::

    transmission-mcp
"""

import argparse
from pathlib import Path

import fastmcp
from transmission_rpc import Client as TransmissionClient

from transmission_mcp import tools
from transmission_mcp.config import load_config
from transmission_mcp.logging import Logger, make_logger

mcp = fastmcp.FastMCP("transmission-mcp")

_client: TransmissionClient | None = None
_logger: Logger | None = None


@mcp.tool()
def list_torrents() -> dict:
    """List all torrents managed by Transmission, sorted by date added (oldest first).

    Returns:
        A dict with a ``torrents`` key containing a list of torrent summaries.
        Each entry includes: ``added_on`` (ISO 8601), ``name``, ``size``
        (human-readable), ``progress``, ``status``, ``seeds``, ``peers``,
        ``download_speed``, ``upload_speed``, and ``eta`` (HH:MM:SS or N/A).
        When there are no torrents, also includes ``message: "No torrents found"``.
    """
    if _client is None:
        raise RuntimeError("Transmission client not initialized")
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    return tools.list_torrents(_client, _logger)


def main() -> None:
    """Parse CLI arguments, load configuration, and start the MCP server."""
    parser = argparse.ArgumentParser(description="Transmission MCP server")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.toml"),
        help="Path to config.toml (default: config.toml)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    global _client, _logger
    _client = TransmissionClient(
        host=config.transmission.host,
        port=config.transmission.port,
        username=config.transmission.username or None,
        password=config.transmission.password or None,
    )
    _logger = make_logger(config.logging.level)

    mcp.run(
        transport="streamable-http",
        host=config.server.host,
        port=config.server.port,
    )
