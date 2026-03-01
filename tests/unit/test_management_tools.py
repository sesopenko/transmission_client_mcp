"""Unit tests for the torrent management tools (start, stop, remove)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, call

import pytest

from transmission_mcp import tools


def _make_torrent(**overrides) -> MagicMock:
    t = MagicMock()
    t.added_date = datetime(2024, 6, 15, 10, 0, 0, tzinfo=UTC)
    t.name = "Test Torrent"
    t.total_size = 1_073_741_824
    t.id = 1
    for k, v in overrides.items():
        setattr(t, k, v)
    return t


def _make_logger() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# _find_unique_torrent helper
# ---------------------------------------------------------------------------


class TestFindUniqueTorrent:
    def test_returns_torrent_on_exact_match(self):
        torrents = [_make_torrent(name="My Torrent")]
        result = tools._find_unique_torrent(torrents, "My Torrent")
        assert not isinstance(result, dict)

    def test_case_insensitive_match(self):
        torrents = [_make_torrent(name="my torrent")]
        result = tools._find_unique_torrent(torrents, "MY TORRENT")
        assert not isinstance(result, dict)

    def test_no_match_returns_error_dict(self):
        result = tools._find_unique_torrent([], "ghost")
        assert isinstance(result, dict)
        assert "error" in result

    def test_no_match_error_contains_name(self):
        result = tools._find_unique_torrent([], "ghost")
        assert isinstance(result, dict)
        assert "ghost" in result["error"]

    def test_duplicate_returns_error_dict(self):
        t1 = _make_torrent(name="Same")
        t2 = _make_torrent(name="Same")
        result = tools._find_unique_torrent([t1, t2], "same")
        assert isinstance(result, dict)
        assert "error" in result
        assert "matches" in result

    def test_duplicate_matches_include_added_on_and_size(self):
        t1 = _make_torrent(name="Same", added_date=datetime(2024, 1, 1, tzinfo=UTC), total_size=1_000_000_000)
        t2 = _make_torrent(name="Same", added_date=datetime(2024, 2, 1, tzinfo=UTC), total_size=2_000_000_000)
        result = tools._find_unique_torrent([t1, t2], "same")
        assert isinstance(result, dict)
        for match in result["matches"]:
            assert "added_on" in match
            assert "size" in match


# ---------------------------------------------------------------------------
# start_torrent
# ---------------------------------------------------------------------------


class TestStartTorrent:
    def test_success_calls_client_start_torrent(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(id=42)]
        tools.start_torrent(client, _make_logger(), "Test Torrent")
        client.start_torrent.assert_called_once_with(42)

    def test_success_returns_message(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="My Torrent", id=1)]
        result = tools.start_torrent(client, _make_logger(), "My Torrent")
        assert "message" in result
        assert "My Torrent" in result["message"]

    def test_no_match_returns_error(self):
        client = MagicMock()
        client.get_torrents.return_value = []
        result = tools.start_torrent(client, _make_logger(), "ghost")
        assert "error" in result
        client.start_torrent.assert_not_called()

    def test_duplicate_returns_error(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="dup"), _make_torrent(name="dup")]
        result = tools.start_torrent(client, _make_logger(), "dup")
        assert "error" in result
        client.start_torrent.assert_not_called()

    def test_transmission_error_on_get_torrents_reraised(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("conn refused")
        with pytest.raises(Exception, match="conn refused"):
            tools.start_torrent(client, _make_logger(), "anything")

    def test_transmission_error_on_start_reraised(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        client.start_torrent.side_effect = Exception("permission denied")
        with pytest.raises(Exception, match="permission denied"):
            tools.start_torrent(client, _make_logger(), "Test Torrent")

    def test_transmission_error_logged_at_error(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("conn refused")
        logger = _make_logger()
        with pytest.raises(Exception, match="conn refused"):
            tools.start_torrent(client, logger, "anything")
        logger.error.assert_called_once()

    def test_invocation_logged_at_info(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.start_torrent(client, logger, "Test Torrent")
        logger.info.assert_called_once_with("start_torrent invoked", tool="start_torrent", name="Test Torrent")

    def test_result_logged_at_debug(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.start_torrent(client, logger, "Test Torrent")
        logger.debug.assert_called_once()


# ---------------------------------------------------------------------------
# stop_torrent
# ---------------------------------------------------------------------------


class TestStopTorrent:
    def test_success_calls_client_stop_torrent(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(id=7)]
        tools.stop_torrent(client, _make_logger(), "Test Torrent")
        client.stop_torrent.assert_called_once_with(7)

    def test_success_returns_message(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="My Torrent", id=1)]
        result = tools.stop_torrent(client, _make_logger(), "My Torrent")
        assert "message" in result
        assert "My Torrent" in result["message"]

    def test_no_match_returns_error(self):
        client = MagicMock()
        client.get_torrents.return_value = []
        result = tools.stop_torrent(client, _make_logger(), "ghost")
        assert "error" in result
        client.stop_torrent.assert_not_called()

    def test_duplicate_returns_error(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="dup"), _make_torrent(name="dup")]
        result = tools.stop_torrent(client, _make_logger(), "dup")
        assert "error" in result
        client.stop_torrent.assert_not_called()

    def test_transmission_error_on_get_torrents_reraised(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("conn refused")
        with pytest.raises(Exception, match="conn refused"):
            tools.stop_torrent(client, _make_logger(), "anything")

    def test_transmission_error_on_stop_reraised(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        client.stop_torrent.side_effect = Exception("permission denied")
        with pytest.raises(Exception, match="permission denied"):
            tools.stop_torrent(client, _make_logger(), "Test Torrent")

    def test_transmission_error_logged_at_error(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("conn refused")
        logger = _make_logger()
        with pytest.raises(Exception, match="conn refused"):
            tools.stop_torrent(client, logger, "anything")
        logger.error.assert_called_once()

    def test_invocation_logged_at_info(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.stop_torrent(client, logger, "Test Torrent")
        logger.info.assert_called_once_with("stop_torrent invoked", tool="stop_torrent", name="Test Torrent")

    def test_result_logged_at_debug(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.stop_torrent(client, logger, "Test Torrent")
        logger.debug.assert_called_once()


# ---------------------------------------------------------------------------
# remove_torrent
# ---------------------------------------------------------------------------


class TestRemoveTorrent:
    def test_success_calls_client_remove_torrent_without_delete(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(id=3)]
        tools.remove_torrent(client, _make_logger(), "Test Torrent")
        client.remove_torrent.assert_called_once_with(3, delete_data=False)

    def test_success_returns_message(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="My Torrent", id=1)]
        result = tools.remove_torrent(client, _make_logger(), "My Torrent")
        assert "message" in result
        assert "My Torrent" in result["message"]

    def test_no_match_returns_error(self):
        client = MagicMock()
        client.get_torrents.return_value = []
        result = tools.remove_torrent(client, _make_logger(), "ghost")
        assert "error" in result
        client.remove_torrent.assert_not_called()

    def test_duplicate_returns_error(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="dup"), _make_torrent(name="dup")]
        result = tools.remove_torrent(client, _make_logger(), "dup")
        assert "error" in result
        client.remove_torrent.assert_not_called()

    def test_transmission_error_reraised(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("conn refused")
        with pytest.raises(Exception, match="conn refused"):
            tools.remove_torrent(client, _make_logger(), "anything")

    def test_transmission_error_on_remove_reraised(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        client.remove_torrent.side_effect = Exception("rpc error")
        with pytest.raises(Exception, match="rpc error"):
            tools.remove_torrent(client, _make_logger(), "Test Torrent")

    def test_invocation_logged_at_info(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.remove_torrent(client, logger, "Test Torrent")
        logger.info.assert_called_once_with("remove_torrent invoked", tool="remove_torrent", name="Test Torrent")


# ---------------------------------------------------------------------------
# remove_torrent_and_delete_data
# ---------------------------------------------------------------------------


class TestRemoveTorrentAndDeleteData:
    def test_success_calls_client_remove_torrent_with_delete(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(id=5)]
        tools.remove_torrent_and_delete_data(client, _make_logger(), "Test Torrent")
        client.remove_torrent.assert_called_once_with(5, delete_data=True)

    def test_success_returns_message(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="My Torrent", id=1)]
        result = tools.remove_torrent_and_delete_data(client, _make_logger(), "My Torrent")
        assert "message" in result
        assert "My Torrent" in result["message"]

    def test_no_match_returns_error(self):
        client = MagicMock()
        client.get_torrents.return_value = []
        result = tools.remove_torrent_and_delete_data(client, _make_logger(), "ghost")
        assert "error" in result
        client.remove_torrent.assert_not_called()

    def test_duplicate_returns_error(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(name="dup"), _make_torrent(name="dup")]
        result = tools.remove_torrent_and_delete_data(client, _make_logger(), "dup")
        assert "error" in result
        client.remove_torrent.assert_not_called()

    def test_transmission_error_reraised(self):
        client = MagicMock()
        client.get_torrents.side_effect = Exception("conn refused")
        with pytest.raises(Exception, match="conn refused"):
            tools.remove_torrent_and_delete_data(client, _make_logger(), "anything")

    def test_transmission_error_on_remove_reraised(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        client.remove_torrent.side_effect = Exception("rpc error")
        with pytest.raises(Exception, match="rpc error"):
            tools.remove_torrent_and_delete_data(client, _make_logger(), "Test Torrent")

    def test_invocation_logged_at_info(self):
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent()]
        logger = _make_logger()
        tools.remove_torrent_and_delete_data(client, logger, "Test Torrent")
        logger.info.assert_called_once_with(
            "remove_torrent_and_delete_data invoked",
            tool="remove_torrent_and_delete_data",
            name="Test Torrent",
        )

    def test_does_not_call_delete_data_false(self):
        """Verify delete_data=False is never passed (it must be True)."""
        client = MagicMock()
        client.get_torrents.return_value = [_make_torrent(id=9)]
        tools.remove_torrent_and_delete_data(client, _make_logger(), "Test Torrent")
        assert call(9, delete_data=False) not in client.remove_torrent.call_args_list
