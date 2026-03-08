"""FastMCP server entrypoint for the Transmission MCP server.

Run with::

    uv run python -m transmission_mcp

or via the installed script::

    transmission-mcp
"""

import argparse
import atexit
import signal
from pathlib import Path
from typing import TYPE_CHECKING

import fastmcp
from transmission_rpc import Client as TransmissionClient

from transmission_mcp import tools
from transmission_mcp.config import load_config
from transmission_mcp.logging import Logger, make_logger
from transmission_mcp.queue import TorrentQueue

if TYPE_CHECKING:
    pass

mcp = fastmcp.FastMCP("transmission-mcp")

_client: TransmissionClient | None = None
_logger: Logger | None = None
_queue: TorrentQueue | None = None


@mcp.tool()
def list_queued_additions() -> dict:
    """List all torrent additions currently waiting in the queue.

    Returns:
        A dict with a ``jobs`` key containing a list of queued job entries. Each
        entry includes ``job_id``, ``torrent_input``, and ``download_dir``.
        When the queue is empty, also includes ``message: "No jobs queued"``.
    """
    if _queue is None:
        raise RuntimeError("Queue not initialized")
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    return tools.list_queued_additions(_queue, _logger)


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


@mcp.tool()
def add_torrent(torrent_input: str, download_dir: str | None = None) -> dict:
    """Queue a torrent for addition to Transmission by magnet link or HTTP/HTTPS URL.

    Validates the input and queues the torrent for asynchronous addition by a
    background worker. Returns immediately with a job ID for status tracking.

    Args:
        torrent_input: A magnet link (``magnet:?xt=urn:...``) or HTTP/HTTPS URL
            pointing to a ``.torrent`` file. Local file paths are not supported.
        download_dir: Optional directory override for saving torrent files. Must be
            within Transmission's configured default download directory. Omit to use
            the session default.

    Returns:
        A dict with a ``message`` key confirming the torrent was queued and a
        ``job_id`` for tracking the addition status.
    """
    if _client is None:
        raise RuntimeError("Transmission client not initialized")
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    if _queue is None:
        raise RuntimeError("Queue not initialized")
    return tools.add_torrent(_client, _logger, _queue, torrent_input, download_dir)


@mcp.tool()
def get_torrent(name: str) -> dict:
    """Fetch detailed information for a single torrent by name.

    Args:
        name: The exact torrent name to look up (case-insensitive). Use
            ``list_torrents`` to discover torrent names.

    Returns:
        On success: a dict with all ``list_torrents`` fields plus ``save_path``,
        ``ratio``, and ``error_message`` (error string or null).

        On no match: ``{"error": "No torrent found matching '[name]'"}``.

        On duplicate match: ``{"error": "...", "matches": [{"added_on": ..., "size": ...}]}``.
    """
    if _client is None:
        raise RuntimeError("Transmission client not initialized")
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    return tools.get_torrent(_client, _logger, name)


@mcp.tool()
def list_files_for_torrent(torrent_name: str) -> dict:
    """List the files contained in a torrent by name.

    Args:
        torrent_name: The exact torrent name to look up (case-insensitive). Use
            ``list_torrents`` to discover torrent names.

    Returns:
        On success: a dict with a ``files`` key containing a list of file dicts
        (``name``, ``size``, ``progress``).

        On no match: ``{"error": "No torrent found matching '[name]'"}``.

        On duplicate match: ``{"error": "...", "matches": [{"added_on": ..., "size": ...}]}``.
    """
    if _client is None:
        raise RuntimeError("Transmission client not initialized")
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    return tools.list_files_for_torrent(_client, _logger, torrent_name)


@mcp.tool()
def start_torrent(name: str) -> dict:
    """Start or resume a paused torrent by name.

    Args:
        name: The exact torrent name to start (case-insensitive). Use
            ``list_torrents`` to discover torrent names.

    Returns:
        On success: ``{"message": "Torrent '<name>' started successfully"}``.
        On no match: ``{"error": "No torrent found matching '[name]'"}``.
        On duplicate match: ``{"error": "...", "matches": [{"added_on": ..., "size": ...}]}``.
    """
    if _client is None:
        raise RuntimeError("Transmission client not initialized")
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    return tools.start_torrent(_client, _logger, name)


@mcp.tool()
def stop_torrent(name: str) -> dict:
    """Stop or pause an active torrent by name.

    Args:
        name: The exact torrent name to stop (case-insensitive). Use
            ``list_torrents`` to discover torrent names.

    Returns:
        On success: ``{"message": "Torrent '<name>' stopped successfully"}``.
        On no match: ``{"error": "No torrent found matching '[name]'"}``.
        On duplicate match: ``{"error": "...", "matches": [{"added_on": ..., "size": ...}]}``.
    """
    if _client is None:
        raise RuntimeError("Transmission client not initialized")
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    return tools.stop_torrent(_client, _logger, name)


@mcp.tool()
def remove_torrent(name: str) -> dict:
    """Remove a torrent by name, keeping all downloaded data on disk.

    Args:
        name: The exact torrent name to remove (case-insensitive). Use
            ``list_torrents`` to discover torrent names.

    Returns:
        On success: ``{"message": "Torrent '<name>' removed successfully"}``.
        On no match: ``{"error": "No torrent found matching '[name]'"}``.
        On duplicate match: ``{"error": "...", "matches": [{"added_on": ..., "size": ...}]}``.
    """
    if _client is None:
        raise RuntimeError("Transmission client not initialized")
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    return tools.remove_torrent(_client, _logger, name)


@mcp.tool()
def remove_torrent_and_delete_data(name: str) -> dict:
    """Remove a torrent by name and permanently delete all downloaded data.

    Args:
        name: The exact torrent name to remove (case-insensitive). Use
            ``list_torrents`` to discover torrent names.

    Returns:
        On success: ``{"message": "Torrent '<name>' removed and data deleted successfully"}``.
        On no match: ``{"error": "No torrent found matching '[name]'"}``.
        On duplicate match: ``{"error": "...", "matches": [{"added_on": ..., "size": ...}]}``.
    """
    if _client is None:
        raise RuntimeError("Transmission client not initialized")
    if _logger is None:
        raise RuntimeError("Logger not initialized")
    return tools.remove_torrent_and_delete_data(_client, _logger, name)


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

    global _client, _logger, _queue
    _client = TransmissionClient(
        host=config.transmission.host,
        port=config.transmission.port,
        username=config.transmission.username or None,
        password=config.transmission.password or None,
    )
    _logger = make_logger(config.logging.level)
    _queue = TorrentQueue(_client, _logger)

    def _shutdown_handler(signum: int, frame: object) -> None:
        """Signal handler for clean shutdown."""
        if _queue is not None:
            _queue.stop()

    signal.signal(signal.SIGTERM, _shutdown_handler)
    signal.signal(signal.SIGINT, _shutdown_handler)
    atexit.register(lambda: _queue.stop() if _queue is not None else None)

    mcp.run(
        transport="streamable-http",
        host=config.server.host,
        port=config.server.port,
    )
