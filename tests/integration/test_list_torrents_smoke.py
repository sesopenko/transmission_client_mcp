"""Integration smoke test: add a real torrent and confirm it appears in list_torrents."""

from transmission_rpc import Client

from transmission_mcp import tools
from transmission_mcp.logging import make_logger

_SILENT_LOGGER = make_logger("critical")

# Damn Small Linux 2024 RC6 — small, well-seeded public torrent used for integration
# testing. Same URL used by test_add_torrent.py.
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


class TestListTorrentsSmoke:
    def test_added_torrent_appears_in_list_torrents(self, transmission_client: Client) -> None:
        """Add a real torrent via add_torrent and assert it appears in list_torrents.

        Asserts presence only — download progress, seeders, peers, and speeds
        are non-deterministic and are not checked.
        """
        try:
            tools.add_torrent(transmission_client, _SILENT_LOGGER, _DSL_TORRENT_URL)

            list_result = tools.list_torrents(transmission_client, _SILENT_LOGGER)
            torrents = list_result["torrents"]

            names = [t["name"] for t in torrents]
            assert any(name.lower() == _DSL_TORRENT_NAME.lower() for name in names), (
                f"Expected torrent '{_DSL_TORRENT_NAME}' in list_torrents results, got: {names}"
            )
        finally:
            _remove_all_torrents(transmission_client)
