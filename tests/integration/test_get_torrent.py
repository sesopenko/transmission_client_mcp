"""Integration tests for the get_torrent tool against a real Transmission instance."""

from transmission_rpc import Client

from transmission_mcp import tools
from transmission_mcp.logging import make_logger

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


class TestGetTorrentIntegration:
    def test_get_torrent_returns_expected_fields(self, transmission_client: Client) -> None:
        """Add a real torrent and verify get_torrent returns all required fields."""
        try:
            add_result = tools.add_torrent(transmission_client, _SILENT_LOGGER, _DSL_TORRENT_URL)
            # Use the name Transmission actually assigned to avoid hardcoded-name brittleness.
            torrent_name = add_result.get("name") or _DSL_TORRENT_NAME

            result = tools.get_torrent(transmission_client, _SILENT_LOGGER, torrent_name)

            assert "error" not in result, f"Expected success, got error: {result.get('error')}"

            for field in (
                "added_on",
                "name",
                "size",
                "progress",
                "status",
                "seeds",
                "peers",
                "download_speed",
                "upload_speed",
                "eta",
            ):
                assert field in result, f"Missing list_torrents field: {field}"

            assert "save_path" in result
            assert "ratio" in result
            assert "files" in result
            assert "error_message" in result
            assert isinstance(result["files"], list)
        finally:
            _remove_all_torrents(transmission_client)

    def test_get_torrent_no_match_returns_error(self, transmission_client: Client) -> None:
        """Verify no-match error when torrent name does not exist."""
        try:
            result = tools.get_torrent(transmission_client, _SILENT_LOGGER, "nonexistent-torrent-xyz")

            assert "error" in result
            assert "nonexistent-torrent-xyz" in result["error"]
        finally:
            _remove_all_torrents(transmission_client)

    def test_get_torrent_case_insensitive_match(self, transmission_client: Client) -> None:
        """Verify lookup succeeds when name case differs from stored name."""
        try:
            add_result = tools.add_torrent(transmission_client, _SILENT_LOGGER, _DSL_TORRENT_URL)
            torrent_name = add_result.get("name") or _DSL_TORRENT_NAME

            upper_name = torrent_name.upper()
            result = tools.get_torrent(transmission_client, _SILENT_LOGGER, upper_name)

            assert "error" not in result, (
                f"Expected success with uppercase name '{upper_name}', got: {result.get('error')}"
            )
        finally:
            _remove_all_torrents(transmission_client)
