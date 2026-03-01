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
        result = tools.add_torrent(client, _make_logger(), _VALID_MAGNET)
        assert result["message"] == "Torrent added successfully"

    def test_no_name_field_for_magnet(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _VALID_MAGNET)
        assert "name" not in result

    def test_no_status_field_for_magnet(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _VALID_MAGNET)
        assert "status" not in result

    def test_no_size_field_for_magnet(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _VALID_MAGNET)
        assert "size" not in result

    def test_calls_add_torrent_with_magnet_input(self):
        client = _make_client()
        tools.add_torrent(client, _make_logger(), _VALID_MAGNET)
        client.add_torrent.assert_called_once()
        call_kwargs = client.add_torrent.call_args.kwargs
        assert call_kwargs.get("torrent") == _VALID_MAGNET


class TestAddTorrentUrlValid:
    def test_returns_success_message(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _VALID_URL)
        assert result["message"] == "Torrent added successfully"

    def test_returns_torrent_name(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _VALID_URL)
        assert result["name"] == "Example Torrent"

    def test_returns_torrent_status(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _VALID_URL)
        assert result["status"] == "downloading"

    def test_returns_human_readable_size(self):
        client = _make_client()
        result = tools.add_torrent(client, _make_logger(), _VALID_URL)
        assert result["size"] == "1.0 GB"

    def test_calls_add_torrent_with_url_input(self):
        client = _make_client()
        tools.add_torrent(client, _make_logger(), _VALID_URL)
        client.add_torrent.assert_called_once()
        call_kwargs = client.add_torrent.call_args.kwargs
        assert call_kwargs.get("torrent") == _VALID_URL


class TestAddTorrentInvalidInput:
    def test_ftp_url_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError, match="magnet link"):
            tools.add_torrent(client, _make_logger(), _FTP_URL)

    def test_plain_string_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError, match="magnet link"):
            tools.add_torrent(client, _make_logger(), _PLAIN_STRING)

    def test_magnet_without_xt_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError, match="xt=urn"):
            tools.add_torrent(client, _make_logger(), _MAGNET_NO_XT)

    def test_magnet_with_non_urn_xt_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError, match="xt=urn"):
            tools.add_torrent(client, _make_logger(), _MAGNET_XT_NO_URN)

    def test_empty_string_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError):
            tools.add_torrent(client, _make_logger(), "")

    def test_invalid_input_does_not_contact_transmission(self):
        client = _make_client()
        with pytest.raises(ValueError):
            tools.add_torrent(client, _make_logger(), _FTP_URL)
        client.add_torrent.assert_not_called()


class TestAddTorrentDownloadDir:
    def test_in_bounds_dir_is_accepted(self):
        client = _make_client(default_dir="/downloads")
        result = tools.add_torrent(client, _make_logger(), _VALID_URL, download_dir="/downloads/movies")
        assert result["message"] == "Torrent added successfully"

    def test_same_as_default_dir_is_accepted(self):
        client = _make_client(default_dir="/downloads")
        result = tools.add_torrent(client, _make_logger(), _VALID_URL, download_dir="/downloads")
        assert result["message"] == "Torrent added successfully"

    def test_out_of_bounds_dir_raises_value_error(self):
        client = _make_client(default_dir="/downloads")
        with pytest.raises(ValueError, match="outside"):
            tools.add_torrent(client, _make_logger(), _VALID_URL, download_dir="/tmp/files")

    def test_sibling_dir_prefix_is_rejected(self):
        """'/downloadssomething' is NOT within '/downloads' (component boundary)."""
        client = _make_client(default_dir="/downloads")
        with pytest.raises(ValueError, match="outside"):
            tools.add_torrent(client, _make_logger(), _VALID_URL, download_dir="/downloadssomething")

    def test_session_failure_skips_dir_check(self):
        """When get_session() raises, any download_dir is accepted."""
        client = _make_client()
        client.get_session.side_effect = Exception("Cannot connect")
        result = tools.add_torrent(client, _make_logger(), _VALID_URL, download_dir="/tmp/files")
        assert result["message"] == "Torrent added successfully"

    def test_no_download_dir_skips_check(self):
        client = _make_client(default_dir="/downloads")
        result = tools.add_torrent(client, _make_logger(), _VALID_URL)
        assert result["message"] == "Torrent added successfully"


class TestAddTorrentDuplicate:
    def test_duplicate_error_returns_success(self):
        client = _make_client()
        client.add_torrent.side_effect = Exception("duplicate torrent")
        result = tools.add_torrent(client, _make_logger(), _VALID_URL)
        assert result["message"] == "Torrent added successfully"

    def test_duplicate_magnet_returns_success(self):
        client = _make_client()
        client.add_torrent.side_effect = Exception("duplicate torrent")
        result = tools.add_torrent(client, _make_logger(), _VALID_MAGNET)
        assert result["message"] == "Torrent added successfully"

    def test_non_duplicate_error_is_reraised(self):
        client = _make_client()
        client.add_torrent.side_effect = Exception("Connection refused")
        with pytest.raises(Exception, match="Connection refused"):
            tools.add_torrent(client, _make_logger(), _VALID_URL)

    def test_non_duplicate_error_logged_at_error(self):
        client = _make_client()
        client.add_torrent.side_effect = Exception("Connection refused")
        logger = _make_logger()
        with pytest.raises(Exception, match="Connection refused"):
            tools.add_torrent(client, logger, _VALID_URL)
        logger.error.assert_called_once()


class TestAddTorrentLogging:
    def test_invocation_logged_at_info(self):
        client = _make_client()
        logger = _make_logger()
        tools.add_torrent(client, logger, _VALID_URL)
        logger.info.assert_called_once_with("add_torrent invoked", tool="add_torrent", input=_VALID_URL)

    def test_result_logged_at_debug(self):
        client = _make_client()
        logger = _make_logger()
        tools.add_torrent(client, logger, _VALID_URL)
        logger.debug.assert_called()

    def test_transmission_error_logged_at_error_level(self):
        client = _make_client()
        client.add_torrent.side_effect = Exception("Timeout")
        logger = _make_logger()
        with pytest.raises(Exception, match="Timeout"):
            tools.add_torrent(client, logger, _VALID_URL)
        logger.error.assert_called_once()
