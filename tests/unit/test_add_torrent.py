"""Unit tests for the add_torrent tool."""

from unittest.mock import MagicMock

import pytest

from transmission_mcp import tools

_VALID_MAGNET = "magnet:?xt=urn:btih:AABB1234AABB1234AABB1234AABB1234AABB1234&dn=Example+Torrent"
_VALID_URL = "https://example.com/file.torrent"
_MAGNET_NO_XT = "magnet:?dn=NoXT"
_MAGNET_XT_NO_URN = "magnet:?xt=NOT_A_URN&dn=Bad"
_FTP_URL = "ftp://example.com/file.torrent"
_PLAIN_STRING = "not-a-torrent-at-all"


def _make_logger() -> MagicMock:
    return MagicMock()


def _make_queue() -> MagicMock:
    """Return a mock queue with a job return value."""
    queue = MagicMock()
    job = MagicMock()
    job.id = "test-uuid-1234"
    queue.enqueue.return_value = job
    return queue


def _make_client(
    default_dir: str | None = "/downloads",
    start_added: bool = True,
) -> MagicMock:
    """Return a mock Transmission client with sensible session defaults."""
    client = MagicMock()
    session = MagicMock()
    session.download_dir = default_dir
    session.start_added_torrents = start_added
    client.get_session.return_value = session

    torrent = MagicMock()
    torrent.id = 42
    torrent.name = "Example Torrent"
    torrent.status = "downloading"
    torrent.total_size = 1_073_741_824  # 1 GB
    client.add_torrent.return_value = torrent
    # get_torrent returns the same mock (add_torrent only gives id/name/hashString;
    # the tool fetches the full torrent for URL inputs).
    client.get_torrent.return_value = torrent

    return client


class TestAddTorrentMagnetValid:
    def test_returns_success_message(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_MAGNET)
        assert result["message"] == "Torrent queued successfully"

    def test_returns_job_id(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_MAGNET)
        assert "job_id" in result
        assert result["job_id"] == "test-uuid-1234"

    def test_no_name_field_in_response(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_MAGNET)
        assert "name" not in result

    def test_no_status_field_in_response(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_MAGNET)
        assert "status" not in result

    def test_no_size_field_in_response(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_MAGNET)
        assert "size" not in result


class TestAddTorrentUrlValid:
    def test_returns_success_message(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_URL)
        assert result["message"] == "Torrent queued successfully"

    def test_returns_job_id(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_URL)
        assert "job_id" in result
        assert result["job_id"] == "test-uuid-1234"


class TestAddTorrentInvalidInput:
    def test_ftp_url_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError, match="magnet link"):
            tools.add_torrent(client, _make_logger(), _make_queue(), _FTP_URL)

    def test_plain_string_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError, match="magnet link"):
            tools.add_torrent(client, _make_logger(), _make_queue(), _PLAIN_STRING)

    def test_magnet_without_xt_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError, match="xt=urn"):
            tools.add_torrent(client, _make_logger(), _make_queue(), _MAGNET_NO_XT)

    def test_magnet_with_non_urn_xt_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError, match="xt=urn"):
            tools.add_torrent(client, _make_logger(), _make_queue(), _MAGNET_XT_NO_URN)

    def test_empty_string_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError):
            tools.add_torrent(client, _make_logger(), _make_queue(), "")

    def test_invalid_input_does_not_enqueue(self):
        client = _make_client()
        queue = _make_queue()
        with pytest.raises(ValueError):
            tools.add_torrent(client, _make_logger(), queue, _FTP_URL)
        queue.enqueue.assert_not_called()


class TestAddTorrentDownloadDir:
    def test_in_bounds_dir_is_accepted(self):
        client = _make_client(default_dir="/downloads")
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_URL, download_dir="/downloads/movies")
        assert result["message"] == "Torrent queued successfully"

    def test_same_as_default_dir_is_accepted(self):
        client = _make_client(default_dir="/downloads")
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_URL, download_dir="/downloads")
        assert result["message"] == "Torrent queued successfully"

    def test_out_of_bounds_dir_raises_value_error(self):
        client = _make_client(default_dir="/downloads")
        with pytest.raises(ValueError, match="outside"):
            tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_URL, download_dir="/tmp/files")

    def test_sibling_dir_prefix_is_rejected(self):
        """'/downloadssomething' is NOT within '/downloads' (component boundary)."""
        client = _make_client(default_dir="/downloads")
        with pytest.raises(ValueError, match="outside"):
            tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_URL, download_dir="/downloadssomething")

    def test_session_failure_skips_dir_check(self):
        """When get_session() raises, any download_dir is accepted."""
        client = _make_client()
        client.get_session.side_effect = Exception("Cannot connect")
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_URL, download_dir="/tmp/files")
        assert result["message"] == "Torrent queued successfully"

    def test_no_download_dir_skips_check(self):
        client = _make_client(default_dir="/downloads")
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_URL)
        assert result["message"] == "Torrent queued successfully"


class TestAddTorrentLogging:
    def test_invocation_logged_at_info(self):
        client = _make_client()
        logger = _make_logger()
        tools.add_torrent(client, logger, _make_queue(), _VALID_URL)
        logger.info.assert_called_once_with("add_torrent invoked", tool="add_torrent", input=_VALID_URL)


class TestAddTorrentQueued:
    def test_returns_queued_message(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_MAGNET)
        assert result["message"] == "Torrent queued successfully"

    def test_returns_job_id(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_MAGNET)
        assert "job_id" in result
        assert isinstance(result["job_id"], str)

    def test_calls_enqueue_with_torrent_input(self):
        client = _make_client()
        queue = _make_queue()
        tools.add_torrent(client, _make_logger(), queue, _VALID_MAGNET)
        queue.enqueue.assert_called_once()
        call_args = queue.enqueue.call_args
        assert call_args[0][0] == _VALID_MAGNET

    def test_calls_enqueue_with_download_dir(self):
        client = _make_client()
        queue = _make_queue()
        download_dir = "/downloads/movies"
        tools.add_torrent(client, _make_logger(), queue, _VALID_MAGNET, download_dir)
        queue.enqueue.assert_called_once()
        call_args = queue.enqueue.call_args
        assert call_args[0][1] == download_dir

    def test_invalid_input_does_not_enqueue(self):
        client = _make_client()
        queue = _make_queue()
        with pytest.raises(ValueError):
            tools.add_torrent(client, _make_logger(), queue, _FTP_URL)
        queue.enqueue.assert_not_called()

    def test_invalid_download_dir_does_not_enqueue(self):
        client = _make_client(default_dir="/downloads")
        queue = _make_queue()
        with pytest.raises(ValueError):
            tools.add_torrent(client, _make_logger(), queue, _VALID_MAGNET, "/tmp/files")
        queue.enqueue.assert_not_called()

    def test_does_not_call_transmission_directly(self):
        client = _make_client()
        tools.add_torrent(client, _make_logger(), _make_queue(), _VALID_MAGNET)
        client.add_torrent.assert_not_called()
