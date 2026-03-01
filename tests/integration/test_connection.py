"""Smoke tests for the Docker integration test harness."""

from transmission_rpc import Client


def test_connection_smoke(transmission_client: Client) -> None:
    """Assert that the Transmission RPC interface is reachable and returns session info."""
    session = transmission_client.get_session()
    assert session is not None
