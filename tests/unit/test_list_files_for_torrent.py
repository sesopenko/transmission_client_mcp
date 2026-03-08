"""Unit tests for the list_files_for_torrent tool."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from transmission_mcp import tools


def _make_file(name: str = "file.iso", size: int = 1_073_741_824, completed: int = 0) -> MagicMock:
    f = MagicMock()
    f.name = name
    f.size = size
    f.completed = completed
    return f


def _make_torrent(**overrides) -> MagicMock:
    t = MagicMock()
    t.added_date = datetime(2024, 6, 15, 10, 0, 0, tzinfo=UTC)
    t.name = "Test Torrent"
    t.total_size = 1_073_741_824  # 1 GB
    t.percent_done = 1.0
    t.status = "seeding"
    t.peers = []
    t.rate_download = 0
    t.rate_upload = 0
    t.eta = None
    t.tracker_stats = []
    t.download_dir = "/downloads/movies"
    t.upload_ratio = 1.24
    t.error = 0
    t.error_string = ""
    t.get_files.return_value = []
    for k, v in overrides.items():
        setattr(t, k, v)
    return t


def _make_logger() -> MagicMock:
    return MagicMock()


class TestListFilesForTorrentNormalCase:
    def test_returns_files_list(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        result = tools.list_files_for_torrent(client, _make_logger(), "Test Torrent")
        assert "files" in result
        assert isinstance(result["files"], list)

    def test_files_list_empty_when_no_files(self):
        client = MagicMock()
        t = _make_torrent()
        t.get_files.return_value = []
        client.get_torrents.return_value = [t]
        result = tools.list_files_for_torrent(client, _make_logger(), "Test Torrent")
        assert result["files"] == []

    def test_files_list_contains_expected_fields(self):
        client = MagicMock()
        t = _make_torrent()
        t.get_files.return_value = [_make_file(name="disc1.iso", size=2_147_483_648, completed=1_073_741_824)]
        client.get_torrents.return_value = [t]
        result = tools.list_files_for_torrent(client, _make_logger(), "Test Torrent")
        assert len(result["files"]) == 1
        f = result["files"][0]
        assert f["name"] == "disc1.iso"
        assert f["size"] == "2.0 GB"
        assert f["progress"] == "50.0%"

    def test_files_progress_zero_when_size_is_zero(self):
        client = MagicMock()
        t = _make_torrent()
        t.get_files.return_value = [_make_file(size=0, completed=0)]
        client.get_torrents.return_value = [t]
        result = tools.list_files_for_torrent(client, _make_logger(), "Test Torrent")
        assert result["files"][0]["progress"] == "0.0%"

    def test_files_progress_50_percent(self):
        client = MagicMock()
        t = _make_torrent()
        t.get_files.return_value = [_make_file(size=1_000_000, completed=500_000)]
        client.get_torrents.return_value = [t]
        result = tools.list_files_for_torrent(client, _make_logger(), "Test Torrent")
        assert result["files"][0]["progress"] == "50.0%"

    def test_files_progress_100_when_complete(self):
        client = MagicMock()
        t = _make_torrent()
        t.get_files.return_value = [_make_file(size=1_000_000, completed=1_000_000)]
        client.get_torrents.return_value = [t]
        result = tools.list_files_for_torrent(client, _make_logger(), "Test Torrent")
        assert result["files"][0]["progress"] == "100.0%"

    def test_invocation_logged_at_info(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.list_files_for_torrent(client, logger, "Test Torrent")
        logger.info.assert_called_once_with(
            "list_files_for_torrent invoked", tool="list_files_for_torrent", torrent_name="Test Torrent"
        )

    def test_result_logged_at_debug(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.list_files_for_torrent(client, logger, "Test Torrent")
        logger.debug.assert_called_once()


class TestListFilesForTorrentCaseInsensitive:
    def test_matches_uppercase_name(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="dsl-2024.rc6.iso")]
        result = tools.list_files_for_torrent(client, _make_logger(), "DSL-2024.RC6.ISO")
        assert "error" not in result

    def test_matches_lowercase_name(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="DSL-2024.RC6.ISO")]
        result = tools.list_files_for_torrent(client, _make_logger(), "dsl-2024.rc6.iso")
        assert "error" not in result

    def test_matches_mixed_case(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="Example Torrent")]
        result = tools.list_files_for_torrent(client, _make_logger(), "EXAMPLE TORRENT")
        assert "error" not in result


class TestListFilesForTorrentNoMatch:
    def test_returns_error_dict(self):
        client = MagicMock()
        client.get_torrents.return_value = []
        result = tools.list_files_for_torrent(client, _make_logger(), "nonexistent")
        assert "error" in result

    def test_error_message_contains_name(self):
        client = MagicMock()
        client.get_torrents.return_value = []
        result = tools.list_files_for_torrent(client, _make_logger(), "My Missing Torrent")
        assert "My Missing Torrent" in result["error"]

    def test_error_message_format(self):
        client = MagicMock()
        client.get_torrents.return_value = []
        result = tools.list_files_for_torrent(client, _make_logger(), "ghost")
        assert result["error"] == "No torrent found matching '[ghost]'"


class TestListFilesForTorrentDuplicateMatch:
    def test_returns_error_dict(self):
        client = MagicMock()
        t1 = _make_torrent(name="Same Name", added_date=datetime(2024, 1, 1, tzinfo=UTC), total_size=1_000_000_000)
        t2 = _make_torrent(name="Same Name", added_date=datetime(2024, 2, 1, tzinfo=UTC), total_size=2_000_000_000)
        client.get_torrents.return_value = [t1, t2]
        result = tools.list_files_for_torrent(client, _make_logger(), "Same Name")
        assert "error" in result

    def test_duplicate_error_message_contains_name(self):
        client = MagicMock()
        t1 = _make_torrent(name="Same Name")
        t2 = _make_torrent(name="same name")
        client.get_torrents.return_value = [t1, t2]
        result = tools.list_files_for_torrent(client, _make_logger(), "same name")
        assert "Same Name" in result["error"] or "same name" in result["error"]

    def test_duplicate_result_includes_matches_list(self):
        client = MagicMock()
        t1 = _make_torrent(name="Same Name", added_date=datetime(2024, 1, 1, tzinfo=UTC), total_size=1_000_000_000)
        t2 = _make_torrent(name="Same Name", added_date=datetime(2024, 2, 1, tzinfo=UTC), total_size=2_000_000_000)
        client.get_torrents.return_value = [t1, t2]
        result = tools.list_files_for_torrent(client, _make_logger(), "Same Name")
        assert "matches" in result
        assert len(result["matches"]) == 2

    def test_duplicate_matches_include_added_on_and_size(self):
        client = MagicMock()
        t1 = _make_torrent(name="Same Name", added_date=datetime(2024, 1, 1, tzinfo=UTC), total_size=1_073_741_824)
        t2 = _make_torrent(name="Same Name", added_date=datetime(2024, 2, 1, tzinfo=UTC), total_size=2_147_483_648)
        client.get_torrents.return_value = [t1, t2]
        result = tools.list_files_for_torrent(client, _make_logger(), "Same Name")
        for match in result["matches"]:
            assert "added_on" in match
            assert "size" in match


class TestListFilesForTorrentTransmissionError:
    def test_transmission_error_is_reraised(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("Connection refused")
        with pytest.raises(Exception, match="Connection refused"):
            tools.list_files_for_torrent(client, _make_logger(), "anything")

    def test_transmission_error_logged_at_error(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("Connection refused")
        logger = _make_logger()
        with pytest.raises(Exception, match="Connection refused"):
            tools.list_files_for_torrent(client, logger, "anything")
        logger.error.assert_called_once()
