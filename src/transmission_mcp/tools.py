"""MCP tool implementations for the Transmission MCP server."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

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
    logger.info("list_torrents invoked", tool="list_torrents")
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


def add_torrent(
    client: Client,
    logger: Logger,
    torrent_input: str,
    download_dir: str | None = None,
) -> dict:
    """Add a torrent to Transmission by magnet link or HTTP/HTTPS URL.

    Args:
        client: Transmission RPC client connected to a running Transmission instance.
        logger: Structured logger for recording invocations and results.
        torrent_input: A magnet link (``magnet:?xt=urn:...``) or HTTP/HTTPS URL
            pointing to a ``.torrent`` file.
        download_dir: Optional directory override for saving torrent files. Must be
            within Transmission's configured default download directory. Omit to use
            the session default.

    Returns:
        A dict with a ``message`` key confirming success. For HTTP/HTTPS URL inputs,
        also includes ``name``, ``status``, and ``size`` (human-readable) once
        Transmission has resolved the torrent metadata. Magnet link responses contain
        only ``message`` because metadata requires peer discovery.

    Raises:
        ValueError: If ``torrent_input`` is not a valid magnet link or HTTP/HTTPS URL,
            or if ``download_dir`` is outside Transmission's default download directory.
        Exception: If the Transmission RPC call fails with a non-duplicate error
            (logged at ``error`` before re-raising so the caller receives it verbatim).
    """
    logger.info("add_torrent invoked", tool="add_torrent", input=torrent_input)
    _validate_torrent_input(torrent_input)

    if download_dir is not None:
        _validate_download_dir(client, download_dir)

    paused = _resolve_paused(client)
    is_magnet = torrent_input.startswith("magnet:")

    kwargs: dict[str, Any] = {"torrent": torrent_input, "paused": paused}
    if download_dir is not None:
        kwargs["download_dir"] = download_dir

    try:
        torrent = client.add_torrent(**kwargs)
    except Exception as exc:
        if "duplicate" in str(exc).lower():
            logger.debug("add_torrent duplicate torrent, treating as success")
            return {"message": "Torrent added successfully"}
        logger.error("Transmission error in add_torrent", error=str(exc))
        raise

    if is_magnet:
        logger.debug("add_torrent result", type="magnet")
        return {"message": "Torrent added successfully"}

    # The torrent-add RPC response only contains id/name/hashString; fetch the
    # full torrent to obtain status and total_size.
    full_torrent = client.get_torrent(torrent.id)
    name = full_torrent.name or ""
    status = full_torrent.status or ""
    size = _human_readable_size(full_torrent.total_size or 0)
    logger.debug("add_torrent result", name=name, status=status)
    return {
        "message": "Torrent added successfully",
        "name": name,
        "status": status,
        "size": size,
    }


def get_torrent(client: Client, logger: Logger, name: str) -> dict:
    """Fetch detailed information for a single torrent by case-insensitive name match.

    Args:
        client: Transmission RPC client connected to a running Transmission instance.
        logger: Structured logger for recording invocations and results.
        name: Torrent name to look up. Matched case-insensitively against exact names.

    Returns:
        On success: a dict containing all ``list_torrents`` fields for the matched
        torrent, plus ``save_path`` (string), ``ratio`` (formatted string),
        ``files`` (list of dicts with ``name``, ``size``, and ``progress``), and
        ``error_message`` (error string or null).

        On no match: ``{"error": "No torrent found matching '[name]'"}``.

        On duplicate match: ``{"error": "Multiple torrents found matching '[name]'",
        "matches": [{"added_on": ..., "size": ...}, ...]}``.

    Raises:
        Exception: If the Transmission RPC call fails (logged at ``error`` before
            re-raising so the error propagates to the MCP client verbatim).
    """
    logger.info("get_torrent invoked", tool="get_torrent", name=name)
    try:
        torrents = client.get_torrents()
    except Exception as exc:
        logger.error("Transmission error in get_torrent", error=str(exc))
        raise

    found = _find_unique_torrent(torrents, name)
    if isinstance(found, dict):
        return found

    torrent = found
    result = _format_torrent(torrent)
    result["save_path"] = torrent.download_dir or ""
    ratio_val = torrent.upload_ratio
    result["ratio"] = f"{ratio_val:.2f}" if ratio_val is not None and ratio_val >= 0 else "0.00"
    result["files"] = _format_files(torrent)
    result["error_message"] = torrent.error_string if torrent.error else None

    logger.debug("get_torrent result", name=torrent.name)
    return result


def start_torrent(client: Client, logger: Logger, name: str) -> dict:
    """Start or resume a paused torrent by case-insensitive name match.

    Args:
        client: Transmission RPC client connected to a running Transmission instance.
        logger: Structured logger for recording invocations and results.
        name: Torrent name to start. Matched case-insensitively against exact names.

    Returns:
        On success: ``{"message": "Torrent '<name>' started successfully"}``.
        On no match: ``{"error": "No torrent found matching '[name]'"}``.
        On duplicate match: ``{"error": "Multiple torrents found matching '[name]'",
        "matches": [{"added_on": ..., "size": ...}, ...]}``.

    Raises:
        Exception: If the Transmission RPC call fails (logged at ``error`` before
            re-raising so the error propagates to the MCP client verbatim).
    """
    logger.info("start_torrent invoked", tool="start_torrent", name=name)
    try:
        torrents = client.get_torrents()
    except Exception as exc:
        logger.error("Transmission error in start_torrent", error=str(exc))
        raise

    found = _find_unique_torrent(torrents, name)
    if isinstance(found, dict):
        return found

    try:
        client.start_torrent(found.id)
    except Exception as exc:
        logger.error("Transmission error in start_torrent", error=str(exc))
        raise

    torrent_name = found.name or name
    logger.debug("start_torrent result", name=torrent_name)
    return {"message": f"Torrent '{torrent_name}' started successfully"}


def stop_torrent(client: Client, logger: Logger, name: str) -> dict:
    """Stop or pause an active torrent by case-insensitive name match.

    Args:
        client: Transmission RPC client connected to a running Transmission instance.
        logger: Structured logger for recording invocations and results.
        name: Torrent name to stop. Matched case-insensitively against exact names.

    Returns:
        On success: ``{"message": "Torrent '<name>' stopped successfully"}``.
        On no match: ``{"error": "No torrent found matching '[name]'"}``.
        On duplicate match: ``{"error": "Multiple torrents found matching '[name]'",
        "matches": [{"added_on": ..., "size": ...}, ...]}``.

    Raises:
        Exception: If the Transmission RPC call fails (logged at ``error`` before
            re-raising so the error propagates to the MCP client verbatim).
    """
    logger.info("stop_torrent invoked", tool="stop_torrent", name=name)
    try:
        torrents = client.get_torrents()
    except Exception as exc:
        logger.error("Transmission error in stop_torrent", error=str(exc))
        raise

    found = _find_unique_torrent(torrents, name)
    if isinstance(found, dict):
        return found

    try:
        client.stop_torrent(found.id)
    except Exception as exc:
        logger.error("Transmission error in stop_torrent", error=str(exc))
        raise

    torrent_name = found.name or name
    logger.debug("stop_torrent result", name=torrent_name)
    return {"message": f"Torrent '{torrent_name}' stopped successfully"}


def remove_torrent(client: Client, logger: Logger, name: str) -> dict:
    """Remove a torrent by case-insensitive name match, keeping downloaded data.

    Args:
        client: Transmission RPC client connected to a running Transmission instance.
        logger: Structured logger for recording invocations and results.
        name: Torrent name to remove. Matched case-insensitively against exact names.

    Returns:
        On success: ``{"message": "Torrent '<name>' removed successfully"}``.
        On no match: ``{"error": "No torrent found matching '[name]'"}``.
        On duplicate match: ``{"error": "Multiple torrents found matching '[name]'",
        "matches": [{"added_on": ..., "size": ...}, ...]}``.

    Raises:
        Exception: If the Transmission RPC call fails (logged at ``error`` before
            re-raising so the error propagates to the MCP client verbatim).
    """
    logger.info("remove_torrent invoked", tool="remove_torrent", name=name)
    try:
        torrents = client.get_torrents()
    except Exception as exc:
        logger.error("Transmission error in remove_torrent", error=str(exc))
        raise

    found = _find_unique_torrent(torrents, name)
    if isinstance(found, dict):
        return found

    try:
        client.remove_torrent(found.id, delete_data=False)
    except Exception as exc:
        logger.error("Transmission error in remove_torrent", error=str(exc))
        raise

    torrent_name = found.name or name
    logger.debug("remove_torrent result", name=torrent_name)
    return {"message": f"Torrent '{torrent_name}' removed successfully"}


def remove_torrent_and_delete_data(client: Client, logger: Logger, name: str) -> dict:
    """Remove a torrent and permanently delete all downloaded data.

    Args:
        client: Transmission RPC client connected to a running Transmission instance.
        logger: Structured logger for recording invocations and results.
        name: Torrent name to remove. Matched case-insensitively against exact names.

    Returns:
        On success: ``{"message": "Torrent '<name>' removed and data deleted successfully"}``.
        On no match: ``{"error": "No torrent found matching '[name]'"}``.
        On duplicate match: ``{"error": "Multiple torrents found matching '[name]'",
        "matches": [{"added_on": ..., "size": ...}, ...]}``.

    Raises:
        Exception: If the Transmission RPC call fails (logged at ``error`` before
            re-raising so the error propagates to the MCP client verbatim).
    """
    logger.info("remove_torrent_and_delete_data invoked", tool="remove_torrent_and_delete_data", name=name)
    try:
        torrents = client.get_torrents()
    except Exception as exc:
        logger.error("Transmission error in remove_torrent_and_delete_data", error=str(exc))
        raise

    found = _find_unique_torrent(torrents, name)
    if isinstance(found, dict):
        return found

    try:
        client.remove_torrent(found.id, delete_data=True)
    except Exception as exc:
        logger.error("Transmission error in remove_torrent_and_delete_data", error=str(exc))
        raise

    torrent_name = found.name or name
    logger.debug("remove_torrent_and_delete_data result", name=torrent_name)
    return {"message": f"Torrent '{torrent_name}' removed and data deleted successfully"}


def _find_unique_torrent(torrents: list[Torrent], name: str) -> Torrent | dict:
    """Find exactly one torrent matching the given name (case-insensitive).

    Args:
        torrents: Full list of torrents to search.
        name: Name to match case-insensitively.

    Returns:
        The matched ``Torrent`` on a unique match.
        An error dict on no match or duplicate match.
    """
    matches = [t for t in torrents if (t.name or "").lower() == name.lower()]

    if not matches:
        return {"error": f"No torrent found matching '{name}'"}

    if len(matches) > 1:
        match_list = [
            {
                "added_on": t.added_date.isoformat() if t.added_date else None,
                "size": _human_readable_size(t.total_size or 0),
            }
            for t in matches
        ]
        return {
            "error": f"Multiple torrents found matching '{name}'",
            "matches": match_list,
        }

    return matches[0]


def _format_files(torrent: Torrent) -> list[dict]:
    result = []
    for f in torrent.get_files():
        size_bytes = f.size or 0
        completed_bytes = f.completed or 0
        progress = f"{(completed_bytes / size_bytes * 100):.1f}%" if size_bytes > 0 else "0.0%"
        result.append(
            {
                "name": f.name or "",
                "size": _human_readable_size(size_bytes),
                "progress": progress,
            }
        )
    return result


def _validate_torrent_input(torrent_input: str) -> None:
    """Validate that the input is a well-formed magnet link or HTTP/HTTPS URL.

    Args:
        torrent_input: The torrent input string to validate.

    Raises:
        ValueError: If the input is not a valid magnet link or HTTP/HTTPS URL.
    """
    if torrent_input.startswith("magnet:"):
        params = parse_qs(urlparse(torrent_input).query)
        xt_values = params.get("xt", [])
        if not any(v.startswith("urn:") for v in xt_values):
            raise ValueError("Invalid magnet link: must contain at least one 'xt=urn:...' parameter")
    elif torrent_input.startswith(("http://", "https://")):
        if not urlparse(torrent_input).netloc:
            raise ValueError("Invalid URL: missing host")
    else:
        raise ValueError("Input must be a magnet link (magnet:?xt=urn:...) or HTTP/HTTPS URL")


def _validate_download_dir(client: Client, download_dir: str) -> None:
    """Enforce that download_dir is within Transmission's default download directory.

    Args:
        client: Transmission RPC client used to fetch the session default directory.
        download_dir: The requested download directory path to validate.

    Raises:
        ValueError: If ``download_dir`` is outside Transmission's default directory.
    """
    try:
        default_dir: str | None = client.get_session().download_dir
    except Exception:
        return  # Session not accessible; skip check

    if not default_dir:
        return

    try:
        Path(download_dir).relative_to(Path(default_dir))
    except ValueError:
        raise ValueError(
            f"download_dir '{download_dir}' is outside the Transmission default download directory '{default_dir}'"
        ) from None


def _resolve_paused(client: Client) -> bool:
    """Determine whether to add the torrent in paused state.

    Reads ``start_added_torrents`` from the Transmission session. Returns ``False``
    (start immediately) if the setting is inaccessible.

    Args:
        client: Transmission RPC client used to fetch session settings.

    Returns:
        ``True`` if the torrent should be added paused, ``False`` otherwise.
    """
    try:
        start_added: bool | None = client.get_session().start_added_torrents
    except Exception:
        return False

    if start_added is None:
        return False
    return not start_added


def _format_torrent(torrent: Torrent) -> dict:
    added_on: str | None = torrent.added_date.isoformat() if torrent.added_date else None
    # torrent.peers is the raw RPC peer array (list of dicts); the library's
    # `-> int` annotation is incorrect — the actual value is list[dict[str, Any]].
    peer_list: list[dict[str, Any]] = cast(list[dict[str, Any]], torrent.peers)
    return {
        "added_on": added_on,
        "name": torrent.name or "",
        "size": _human_readable_size(torrent.total_size or 0),
        "progress": f"{(torrent.percent_done or 0.0) * 100:.1f}%",
        "status": torrent.status or "",
        "seeds": f"{_connected_seeders(peer_list)}/{_tracker_seeder_count(torrent)}",
        "peers": f"{_connected_leechers(peer_list)}/{_tracker_leecher_count(torrent)}",
        "download_speed": _human_readable_speed(torrent.rate_download or 0),
        "upload_speed": _human_readable_speed(torrent.rate_upload or 0),
        "eta": _format_eta(torrent.eta),
    }


def _connected_seeders(peer_list: list[dict[str, Any]]) -> int:
    return sum(1 for p in peer_list if p.get("progress", 0.0) >= 1.0)


def _connected_leechers(peer_list: list[dict[str, Any]]) -> int:
    return sum(1 for p in peer_list if p.get("progress", 0.0) < 1.0)


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
