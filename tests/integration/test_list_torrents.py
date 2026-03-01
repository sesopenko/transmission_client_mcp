"""Integration tests for the list_torrents tool against a real Transmission instance."""

import pytest
from transmission_rpc import Client

from transmission_mcp import tools
from transmission_mcp.logging import make_logger

_SILENT_LOGGER = make_logger("critical")


@pytest.mark.usefixtures("transmission_client")
class TestListTorrentsIntegration:
    def test_returns_dict_with_torrents_key(self, transmission_client: Client):
        result = tools.list_torrents(transmission_client, _SILENT_LOGGER)
        assert isinstance(result, dict)
        assert "torrents" in result

    def test_empty_transmission_returns_empty_list(self, transmission_client: Client):
        result = tools.list_torrents(transmission_client, _SILENT_LOGGER)
        # Fresh Transmission instance has no torrents.
        assert result["torrents"] == []
        assert result.get("message") == "No torrents found"

    def test_torrents_list_is_list(self, transmission_client: Client):
        result = tools.list_torrents(transmission_client, _SILENT_LOGGER)
        assert isinstance(result["torrents"], list)
