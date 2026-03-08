"""Integration tests for the list_files_for_torrent tool against a real Transmission instance."""

from transmission_rpc import Client

from tests.integration.conftest import wait_for_torrent
from transmission_mcp import tools
from transmission_mcp.logging import make_logger
from transmission_mcp.queue import TorrentQueue

_SILENT_LOGGER = make_logger("critical")

# Damn Small Linux 2024 RC6 — small, well-seeded public torrent used for integration
# testing. Same URL used by other integration tests.
_DSL_TORRENT_URL = (
    "https://raw.githubusercontent.com/sesopenko/transmission_client_mcp/main/tests/fixtures/dsl-2024.rc6.iso.torrent"
)
_DSL_TORRENT_NAME = "dsl-2024.rc6.iso"


def _remove_all_torrents(client: Client) -> None:
    try:
        for t in client.get_torrents():
            client.remove_torrent(t.id, delete_data=True)
    except Exception:
        pass


class TestListFilesForTorrentIntegration:
    def test_returns_files_list(self, transmission_client: Client, torrent_queue: TorrentQueue) -> None:
        """Add a real torrent and verify list_files_for_torrent returns files."""
        try:
            tools.add_torrent(transmission_client, _SILENT_LOGGER, torrent_queue, _DSL_TORRENT_URL)
            wait_for_torrent(transmission_client, _DSL_TORRENT_NAME)

            result = tools.list_files_for_torrent(transmission_client, _SILENT_LOGGER, _DSL_TORRENT_NAME)

            assert "error" not in result, f"Expected success, got error: {result.get('error')}"
            assert "files" in result
            assert isinstance(result["files"], list)
        finally:
            _remove_all_torrents(transmission_client)

    def test_no_match_returns_error(self, transmission_client: Client) -> None:
        """Verify no-match error when torrent name does not exist."""
        try:
            result = tools.list_files_for_torrent(transmission_client, _SILENT_LOGGER, "nonexistent-torrent-xyz")

            assert "error" in result
            assert "nonexistent-torrent-xyz" in result["error"]
        finally:
            _remove_all_torrents(transmission_client)

    def test_case_insensitive_match(self, transmission_client: Client, torrent_queue: TorrentQueue) -> None:
        """Verify lookup succeeds when name case differs from stored name."""
        try:
            tools.add_torrent(transmission_client, _SILENT_LOGGER, torrent_queue, _DSL_TORRENT_URL)
            wait_for_torrent(transmission_client, _DSL_TORRENT_NAME)

            upper_name = _DSL_TORRENT_NAME.upper()
            result = tools.list_files_for_torrent(transmission_client, _SILENT_LOGGER, upper_name)

            assert "error" not in result, (
                f"Expected success with uppercase name '{upper_name}', got: {result.get('error')}"
            )
            assert "files" in result
            assert isinstance(result["files"], list)
        finally:
            _remove_all_torrents(transmission_client)
