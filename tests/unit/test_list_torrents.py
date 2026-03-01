"""Unit tests for the list_torrents tool."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from transmission_mcp import tools

# Peer dicts used across tests.  Each has a "progress" key (0.0–1.0) mirroring
# Transmission's raw RPC peer array.  progress >= 1.0 → seeder, < 1.0 → leecher.
_SEEDER = {"progress": 1.0}
_LEECHER_50 = {"progress": 0.5}
_LEECHER_30 = {"progress": 0.3}

# Default peer list: 4 seeders, 2 leechers.
_DEFAULT_PEERS = [_SEEDER, _SEEDER, _SEEDER, _SEEDER, _LEECHER_50, _LEECHER_30]


def _make_torrent(**overrides) -> MagicMock:
    """Return a mock Torrent with sensible defaults."""
    t = MagicMock()
    t.added_date = datetime(2024, 6, 15, 10, 0, 0, tzinfo=UTC)
    t.name = "Example Torrent"
    t.total_size = 1_073_741_824  # 1 GB
    t.percent_done = 0.735
    t.status = "downloading"
    # peers is the raw RPC peer array (list of dicts with at least a "progress" key).
    t.peers = list(_DEFAULT_PEERS)
    t.rate_download = 3_355_443  # ~3.2 MB/s
    t.rate_upload = 1_153_433  # ~1.1 MB/s
    t.eta = timedelta(seconds=3723)  # 1h 2m 3s
    t.tracker_stats = []
    for k, v in overrides.items():
        setattr(t, k, v)
    return t


def _make_logger() -> MagicMock:
    return MagicMock()


class TestListTorrentsNormalCase:
    def test_returns_torrents_key(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        result = tools.list_torrents(client, _make_logger())
        assert "torrents" in result

    def test_no_message_key_when_torrents_present(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        result = tools.list_torrents(client, _make_logger())
        assert "message" not in result

    def test_torrent_fields_present(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        result = tools.list_torrents(client, _make_logger())
        torrent = result["torrents"][0]
        expected_fields = {
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
        }
        assert expected_fields == set(torrent.keys())

    def test_added_on_iso8601(self):
        dt = datetime(2024, 6, 15, 10, 0, 0, tzinfo=UTC)
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(added_date=dt)]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["added_on"] == dt.isoformat()

    def test_added_on_none_when_no_date(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(added_date=None)]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["added_on"] is None

    def test_size_human_readable(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(total_size=1_073_741_824)]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["size"] == "1.0 GB"

    def test_progress_format(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(percent_done=0.735)]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["progress"] == "73.5%"

    def test_eta_format(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(eta=timedelta(seconds=3723))]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["eta"] == "01:02:03"

    def test_eta_na_when_none(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(eta=None)]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["eta"] == "N/A"

    def test_seeds_counts_peers_with_full_progress(self):
        # 3 seeders (progress=1.0), 1 leecher; tracker reports 100 seeders total.
        tracker = MagicMock()
        tracker.seeder_count = 100
        tracker.leecher_count = 0
        peers = [_SEEDER, _SEEDER, _SEEDER, _LEECHER_50]
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(peers=peers, tracker_stats=[tracker])]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["seeds"] == "3/100"

    def test_seeds_zero_connected_when_no_peers(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(peers=[], tracker_stats=[])]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["seeds"] == "0/0"

    def test_peers_counts_peers_with_partial_progress(self):
        # 1 seeder, 2 leechers; tracker reports 51 leechers total.
        tracker = MagicMock()
        tracker.seeder_count = 38
        tracker.leecher_count = 51
        peers = [_SEEDER, _LEECHER_50, _LEECHER_30]
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(peers=peers, tracker_stats=[tracker])]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["peers"] == "2/51"

    def test_peers_zero_connected_when_no_peers(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(peers=[], tracker_stats=[])]
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"][0]["peers"] == "0/0"

    def test_sorted_oldest_first(self):
        newer = _make_torrent(name="Newer", added_date=datetime(2024, 12, 1, tzinfo=UTC))
        older = _make_torrent(name="Older", added_date=datetime(2024, 1, 1, tzinfo=UTC))
        client = MagicMock()
        client.get_torrents.return_value = [newer, older]
        result = tools.list_torrents(client, _make_logger())
        names = [t["name"] for t in result["torrents"]]
        assert names == ["Older", "Newer"]

    def test_invocation_logged_with_tool_metadata(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.list_torrents(client, logger)
        logger.info.assert_called_once_with("list_torrents invoked", tool="list_torrents")

    def test_result_logged_at_debug(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.list_torrents(client, logger)
        logger.debug.assert_called_once()


class TestListTorrentsEmptyCase:
    def test_returns_empty_torrents_list(self):
        client = MagicMock()
        client.get_torrents.return_value = []
        result = tools.list_torrents(client, _make_logger())
        assert result["torrents"] == []

    def test_includes_no_torrents_message(self):
        client = MagicMock()
        client.get_torrents.return_value = []
        result = tools.list_torrents(client, _make_logger())
        assert result.get("message") == "No torrents found"


class TestListTorrentsErrorCase:
    def test_transmission_error_is_reraised(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("Connection refused")
        with pytest.raises(Exception, match="Connection refused"):
            tools.list_torrents(client, _make_logger())

    def test_transmission_error_logged_at_error(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("Connection refused")
        logger = _make_logger()
        with pytest.raises(Exception, match="Connection refused"):
            tools.list_torrents(client, logger)
        logger.error.assert_called_once()


class TestFormatHelpers:
    def test_size_bytes(self):
        assert tools._human_readable_size(512) == "512 B"

    def test_size_kb(self):
        assert tools._human_readable_size(2048) == "2.0 KB"

    def test_size_mb(self):
        assert tools._human_readable_size(5 * 1024**2) == "5.0 MB"

    def test_size_gb(self):
        assert tools._human_readable_size(2 * 1024**3) == "2.0 GB"

    def test_size_tb(self):
        assert tools._human_readable_size(3 * 1024**4) == "3.0 TB"

    def test_speed_includes_per_sec(self):
        assert tools._human_readable_speed(1024) == "1.0 KB/s"

    def test_eta_zero(self):
        assert tools._format_eta(timedelta(seconds=0)) == "00:00:00"

    def test_eta_large(self):
        assert tools._format_eta(timedelta(seconds=90061)) == "25:01:01"

    def test_eta_none_returns_na(self):
        assert tools._format_eta(None) == "N/A"

    def test_connected_seeders_counts_full_progress(self):
        peers = [{"progress": 1.0}, {"progress": 1.0}, {"progress": 0.5}]
        assert tools._connected_seeders(peers) == 2

    def test_connected_seeders_empty_list(self):
        assert tools._connected_seeders([]) == 0

    def test_connected_leechers_counts_partial_progress(self):
        peers = [{"progress": 1.0}, {"progress": 0.5}, {"progress": 0.0}]
        assert tools._connected_leechers(peers) == 2

    def test_connected_leechers_empty_list(self):
        assert tools._connected_leechers([]) == 0

    def test_tracker_seeder_count_empty(self):
        torrent = _make_torrent(tracker_stats=[])
        assert tools._tracker_seeder_count(torrent) == 0

    def test_tracker_seeder_count_uses_max(self):
        s1 = MagicMock()
        s1.seeder_count = 5
        s2 = MagicMock()
        s2.seeder_count = 12
        torrent = _make_torrent(tracker_stats=[s1, s2])
        assert tools._tracker_seeder_count(torrent) == 12

    def test_tracker_seeder_count_ignores_unknown(self):
        s = MagicMock()
        s.seeder_count = -1
        torrent = _make_torrent(tracker_stats=[s])
        assert tools._tracker_seeder_count(torrent) == 0

    def test_tracker_leecher_count_uses_max(self):
        s1 = MagicMock()
        s1.leecher_count = 3
        s2 = MagicMock()
        s2.leecher_count = 8
        torrent = _make_torrent(tracker_stats=[s1, s2])
        assert tools._tracker_leecher_count(torrent) == 8
