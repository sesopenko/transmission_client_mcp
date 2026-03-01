"""Integration test fixtures for the Transmission MCP server.

This harness manages a real Transmission instance via Docker Compose and exposes a
`transmission_rpc.Client` for integration tests.

Design notes (requirements.md):
- Integration tests must run against a real Transmission instance (Docker-based).
- The harness should be established early and be resilient (de-risk feasibility).
"""

import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from transmission_rpc import Client

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_COMPOSE_FILE = _PROJECT_ROOT / "docker-compose.test.yml"


def _detect_compose_cmd() -> list[str]:
    """Return the available Docker Compose command prefix.

    Tries the modern plugin form first ('docker compose'), then the legacy
    standalone binary ('docker-compose'). Raises RuntimeError if neither
    is available so failures are caught early with a clear message.

    Returns:
        List of strings forming the compose command prefix, e.g.
        ``["docker", "compose"]`` or ``["docker-compose"]``.
    """
    for candidate in (["docker", "compose"], ["docker-compose"]):
        try:
            subprocess.run(
                candidate + ["version"],
                check=True,
                capture_output=True,
            )
            return candidate
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("Neither 'docker compose' nor 'docker-compose' is available")


_COMPOSE_CMD = _detect_compose_cmd()

# Keep default localhost mapping, but allow overrides to support CI/remote Docker.
_HOST = os.environ.get("TRANSMISSION_TEST_HOST", "localhost")
_PORT = int(os.environ.get("TRANSMISSION_TEST_PORT", "19091"))

# Credentials: default to None (no auth) to match docker-compose.test.yml, which
# intentionally omits USER/PASS so linuxserver/transmission starts with auth disabled.
# Set these env vars if your image or config requires authentication.
_raw_username = os.environ.get("TRANSMISSION_TEST_USERNAME", "")
_USERNAME: str | None = _raw_username or None
_raw_password = os.environ.get("TRANSMISSION_TEST_PASSWORD", "")
_PASSWORD: str | None = _raw_password or None

# Keep a generous timeout; container image pulls + init can be slow on first run.
_TIMEOUT_SECONDS = int(os.environ.get("TRANSMISSION_TEST_TIMEOUT_SECONDS", "120"))

# Polling cadence: shorter interval reduces overall suite latency on fast machines.
_POLL_INTERVAL_SECONDS = 1.0


@pytest.fixture(scope="session")
def transmission_client() -> Iterator[Client]:
    """Start a Transmission Docker container and yield a connected client.

    Starts the Transmission container defined in docker-compose.test.yml, waits
    until the RPC interface is ready, and yields a connected
    transmission_rpc.Client. Tears down the container after the test session
    ends.
    """
    _compose_up()
    try:
        client = _wait_for_transmission()
        yield client
    finally:
        _compose_down()


def _compose_up() -> None:
    subprocess.run(
        [*_COMPOSE_CMD, "-f", str(_COMPOSE_FILE), "up", "-d", "--wait"],
        check=True,
        cwd=_PROJECT_ROOT,
    )


def _compose_down() -> None:
    subprocess.run(
        [*_COMPOSE_CMD, "-f", str(_COMPOSE_FILE), "down", "-v"],
        check=True,
        cwd=_PROJECT_ROOT,
    )


def _wait_for_transmission() -> Client:
    """Wait until Transmission's RPC interface responds to get_session()."""
    deadline = time.monotonic() + _TIMEOUT_SECONDS
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            client = Client(host=_HOST, port=_PORT, username=_USERNAME, password=_PASSWORD)
            client.get_session()
            return client
        except Exception as exc:  # pragma: no cover (depends on timing/environment)
            last_error = exc
            time.sleep(_POLL_INTERVAL_SECONDS)

    message = f"Transmission RPC did not become ready within {_TIMEOUT_SECONDS} seconds"
    if last_error is not None:
        message = f"{message}; last error: {last_error!r}"
    raise TimeoutError(message)
