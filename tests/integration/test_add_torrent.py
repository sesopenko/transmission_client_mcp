"""Integration tests for the add_torrent tool against a real Transmission instance."""

from transmission_rpc import Client

from tests.integration.conftest import wait_for_torrent
from transmission_mcp import tools
from transmission_mcp.logging import make_logger
from transmission_mcp.queue import TorrentQueue

_SILENT_LOGGER = make_logger("critical")

# Damn Small Linux 2024 RC6 — small, well-seeded public torrent used for integration
# testing the HTTP/HTTPS URL path of add_torrent.
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


class TestAddTorrentUrlIntegration:
    def test_add_url_torrent_returns_expected_shape(
        self, transmission_client: Client, torrent_queue: TorrentQueue
    ) -> None:
        """Add a real .torrent URL and verify the response structure."""
        try:
            result = tools.add_torrent(transmission_client, _SILENT_LOGGER, torrent_queue, _DSL_TORRENT_URL)
            assert result["message"] == "Torrent queued successfully"
            assert "job_id" in result

            # Wait for the torrent to be added and then verify its fields
            wait_for_torrent(transmission_client, _DSL_TORRENT_NAME)
            torrent = tools.get_torrent(transmission_client, _SILENT_LOGGER, _DSL_TORRENT_NAME)

            assert "error" not in torrent
            assert torrent.get("name") == _DSL_TORRENT_NAME
            assert "status" in torrent
            assert "size" in torrent
        finally:
            _remove_all_torrents(transmission_client)
