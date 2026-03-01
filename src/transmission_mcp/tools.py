"""MCP tool implementations for the Transmission MCP server."""

from datetime import UTC, datetime, timedelta

from transmission_rpc import Client, Torrent

from transmission_mcp.logging import Logger

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def list_torrents(client: Client, logger: Logger) -> dict:
    """Return all torrents managed by Transmission, sorted by date added oldest-first.

    Args:
        client: Transmission RPC client connected to a running Transmission instance.
        logger: Structured logger for recording invocations and results.

    Returns:
        A dict with a ``torrents`` key containing a list of torrent summary dicts.
        Each entry includes: ``added_on``, ``name``, ``size``, ``progress``,
        ``status``, ``seeds``, ``peers``, ``download_speed``, ``upload_speed``,
        ``eta``.  When no torrents exist the dict also contains a ``message``
        key set to ``"No torrents found"``.

    Raises:
        Exception: If the Transmission RPC call fails (logged at ``error`` before
            re-raising so the error propagates to the MCP client verbatim).
    """
    logger.info("list_torrents invoked")
    try:
        torrents = client.get_torrents()
    except Exception as exc:
        logger.error("Transmission error in list_torrents", error=str(exc))
        raise

    if not torrents:
        logger.debug("list_torrents result", torrent_count=0)
        return {"torrents": [], "message": "No torrents found"}

    sorted_torrents = sorted(torrents, key=lambda t: t.added_date or _EPOCH)
    result_list = [_format_torrent(t) for t in sorted_torrents]
    logger.debug("list_torrents result", torrent_count=len(result_list))
    return {"torrents": result_list}


def _format_torrent(torrent: Torrent) -> dict:
    added_on = torrent.added_date.isoformat() if torrent.added_date else ""
    return {
        "added_on": added_on,
        "name": torrent.name or "",
        "size": _human_readable_size(torrent.total_size or 0),
        "progress": f"{(torrent.percent_done or 0.0) * 100:.1f}%",
        "status": torrent.status or "",
        "seeds": f"{torrent.peers_sending_to_us or 0}/{_tracker_seeder_count(torrent)}",
        "peers": f"{torrent.peers_getting_from_us or 0}/{_tracker_leecher_count(torrent)}",
        "download_speed": _human_readable_speed(torrent.rate_download or 0),
        "upload_speed": _human_readable_speed(torrent.rate_upload or 0),
        "eta": _format_eta(torrent.eta),
    }


def _human_readable_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.1f} MB"
    if size_bytes < 1024**4:
        return f"{size_bytes / 1024**3:.1f} GB"
    return f"{size_bytes / 1024**4:.1f} TB"


def _human_readable_speed(speed_bps: int) -> str:
    return _human_readable_size(speed_bps) + "/s"


def _format_eta(eta: timedelta | None) -> str:
    if eta is None:
        return "N/A"
    total_seconds = int(eta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _tracker_seeder_count(torrent: Torrent) -> int:
    stats = torrent.tracker_stats
    if not stats:
        return 0
    counts = [s.seeder_count for s in stats if s.seeder_count >= 0]
    return max(counts, default=0)


def _tracker_leecher_count(torrent: Torrent) -> int:
    stats = torrent.tracker_stats
    if not stats:
        return 0
    counts = [s.leecher_count for s in stats if s.leecher_count >= 0]
    return max(counts, default=0)
