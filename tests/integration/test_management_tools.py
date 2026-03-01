"""Integration tests for the torrent management tools against a real Transmission instance."""

from transmission_rpc import Client

from transmission_mcp import tools
from transmission_mcp.logging import make_logger

_SILENT_LOGGER = make_logger("critical")

_DSL_TORRENT_URL = (
    "https://linuxtracker.org/download.php"
    "?id=9a9f19345e31afd1dc9a5caaedf7982459900498"
    "&f=Damn+Small+Linux+2024+RC6+ISO.torrent"
    "&key=6c2d037a"
)
_DSL_TORRENT_NAME = "dsl-2024.rc6.iso"


def _add_dsl_torrent(client: Client) -> str:
    """Add the DSL test torrent and return the name Transmission assigned."""
    result = tools.add_torrent(client, _SILENT_LOGGER, _DSL_TORRENT_URL)
    return result.get("name") or _DSL_TORRENT_NAME


def _remove_all_torrents(client: Client) -> None:
    try:
        for t in client.get_torrents():
            client.remove_torrent(t.id, delete_data=True)
    except Exception:
        pass


class TestStopTorrentIntegration:
    def test_stop_torrent_succeeds(self, transmission_client: Client) -> None:
        """Add a torrent and verify stop_torrent returns a success message."""
        try:
            name = _add_dsl_torrent(transmission_client)
            result = tools.stop_torrent(transmission_client, _SILENT_LOGGER, name)
            assert "error" not in result
            assert "message" in result
        finally:
            _remove_all_torrents(transmission_client)

    def test_stop_torrent_no_match_returns_error(self, transmission_client: Client) -> None:
        try:
            result = tools.stop_torrent(transmission_client, _SILENT_LOGGER, "nonexistent-xyz")
            assert "error" in result
        finally:
            _remove_all_torrents(transmission_client)


class TestStartTorrentIntegration:
    def test_start_torrent_succeeds(self, transmission_client: Client) -> None:
        """Add a torrent, stop it, then start it; verify success message returned."""
        try:
            name = _add_dsl_torrent(transmission_client)
            tools.stop_torrent(transmission_client, _SILENT_LOGGER, name)
            result = tools.start_torrent(transmission_client, _SILENT_LOGGER, name)
            assert "error" not in result
            assert "message" in result
        finally:
            _remove_all_torrents(transmission_client)

    def test_start_torrent_no_match_returns_error(self, transmission_client: Client) -> None:
        try:
            result = tools.start_torrent(transmission_client, _SILENT_LOGGER, "nonexistent-xyz")
            assert "error" in result
        finally:
            _remove_all_torrents(transmission_client)


class TestRemoveTorrentIntegration:
    def test_remove_torrent_removes_from_list(self, transmission_client: Client) -> None:
        """Add a torrent, remove it, and confirm it no longer appears in list_torrents."""
        try:
            name = _add_dsl_torrent(transmission_client)
            result = tools.remove_torrent(transmission_client, _SILENT_LOGGER, name)
            assert "error" not in result
            assert "message" in result

            list_result = tools.list_torrents(transmission_client, _SILENT_LOGGER)
            names = [t["name"] for t in list_result["torrents"]]
            assert name not in names
        finally:
            _remove_all_torrents(transmission_client)

    def test_remove_torrent_no_match_returns_error(self, transmission_client: Client) -> None:
        try:
            result = tools.remove_torrent(transmission_client, _SILENT_LOGGER, "nonexistent-xyz")
            assert "error" in result
        finally:
            _remove_all_torrents(transmission_client)


class TestRemoveTorrentAndDeleteDataIntegration:
    def test_removes_torrent_from_list(self, transmission_client: Client) -> None:
        """Add a torrent, remove-with-delete, and confirm it no longer appears."""
        try:
            name = _add_dsl_torrent(transmission_client)
            result = tools.remove_torrent_and_delete_data(transmission_client, _SILENT_LOGGER, name)
            assert "error" not in result
            assert "message" in result

            list_result = tools.list_torrents(transmission_client, _SILENT_LOGGER)
            names = [t["name"] for t in list_result["torrents"]]
            assert name not in names
        finally:
            _remove_all_torrents(transmission_client)

    def test_no_match_returns_error(self, transmission_client: Client) -> None:
        try:
            result = tools.remove_torrent_and_delete_data(transmission_client, _SILENT_LOGGER, "nonexistent-xyz")
            assert "error" in result
        finally:
            _remove_all_torrents(transmission_client)
