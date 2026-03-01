"""Integration tests for the add_torrent tool against a real Transmission instance."""

from transmission_rpc import Client

from transmission_mcp import tools
from transmission_mcp.logging import make_logger

_SILENT_LOGGER = make_logger("critical")

# Damn Small Linux 2024 RC6 — small, well-seeded public torrent used for integration
# testing the HTTP/HTTPS URL path of add_torrent.
_DSL_TORRENT_URL = (
    "https://linuxtracker.org/download.php"
    "?id=9a9f19345e31afd1dc9a5caaedf7982459900498"
    "&f=Damn+Small+Linux+2024+RC6+ISO.torrent"
    "&key=6c2d037a"
)
_DSL_TORRENT_NAME = "dsl-2024.rc6.iso"


def _remove_all_torrents(client: Client) -> None:
    try:
        for t in client.get_torrents():
            client.remove_torrent(t.id, delete_data=True)
    except Exception:
        pass


class TestAddTorrentUrlIntegration:
    def test_add_url_torrent_returns_expected_shape(self, transmission_client: Client):
        """Add a real .torrent URL and verify the response structure."""
        try:
            result = tools.add_torrent(transmission_client, _SILENT_LOGGER, _DSL_TORRENT_URL)
            assert result["message"] == "Torrent added successfully"
            assert result.get("name") == _DSL_TORRENT_NAME
            assert "status" in result
            assert "size" in result
        finally:
            _remove_all_torrents(transmission_client)
