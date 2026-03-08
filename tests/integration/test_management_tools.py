"""Integration tests for the torrent management tools against a real Transmission instance."""

from transmission_rpc import Client

from tests.integration.conftest import wait_for_torrent
from transmission_mcp import tools
from transmission_mcp.logging import make_logger
from transmission_mcp.queue import TorrentQueue

_SILENT_LOGGER = make_logger("critical")

_DSL_TORRENT_URL = (
    "https://raw.githubusercontent.com/sesopenko/transmission_client_mcp/main/tests/fixtures/dsl-2024.rc6.iso.torrent"
)
_DSL_TORRENT_NAME = "dsl-2024.rc6.iso"


def _add_dsl_torrent(client: Client, queue: TorrentQueue) -> str:
    """Add the DSL test torrent and wait for it to appear, then return the torrent name."""
    tools.add_torrent(client, _SILENT_LOGGER, queue, _DSL_TORRENT_URL)
    wait_for_torrent(client, _DSL_TORRENT_NAME)
    return _DSL_TORRENT_NAME


def _remove_all_torrents(client: Client) -> None:
    try:
        for t in client.get_torrents():
            client.remove_torrent(t.id, delete_data=True)
    except Exception:
        pass


class TestStopTorrentIntegration:
    def test_stop_torrent_succeeds(self, transmission_client: Client, torrent_queue: TorrentQueue) -> None:
        """Add a torrent and verify stop_torrent returns a success message."""
        try:
            name = _add_dsl_torrent(transmission_client, torrent_queue)
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
    def test_start_torrent_succeeds(self, transmission_client: Client, torrent_queue: TorrentQueue) -> None:
        """Add a torrent, stop it, then start it; verify success message returned."""
        try:
            name = _add_dsl_torrent(transmission_client, torrent_queue)
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
    def test_remove_torrent_removes_from_list(self, transmission_client: Client, torrent_queue: TorrentQueue) -> None:
        """Add a torrent, remove it, and confirm it no longer appears in list_torrents."""
        try:
            name = _add_dsl_torrent(transmission_client, torrent_queue)
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
    def test_removes_torrent_from_list(self, transmission_client: Client, torrent_queue: TorrentQueue) -> None:
        """Add a torrent, remove-with-delete, and confirm it no longer appears."""
        try:
            name = _add_dsl_torrent(transmission_client, torrent_queue)
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
