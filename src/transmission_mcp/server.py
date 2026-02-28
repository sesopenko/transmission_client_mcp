"""FastMCP server entrypoint for the Transmission MCP server.

Run with::

    uv run python -m transmission_mcp

or via the installed script::

    transmission-mcp
"""

import argparse
from pathlib import Path

import fastmcp

from transmission_mcp.config import load_config

mcp = fastmcp.FastMCP("transmission-mcp")


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

    mcp.run(
        transport="streamable-http",
        host=config.server.host,
        port=config.server.port,
    )
