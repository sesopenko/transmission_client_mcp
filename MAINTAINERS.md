# Maintainers Guide

Developer reference for setting up and working on this project.

Commands are added to this file as the corresponding functionality is built. Check back as construction phases complete.

---

## Setup

### 1. Install uv

Follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Install dependencies

```bash
uv sync
```

### 3. Install pre-commit hooks

```bash
uv run pre-commit install
```

---

## Code Quality

Run all quality checks manually:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src/
```

These checks also run automatically on every commit via pre-commit hooks.

---

## Running the Server

### Locally

```bash
uv run python -m transmission_mcp
```

Pass `--config <path>` to use a non-default config file location.

### Via Docker

Build the image:

```bash
docker build -t transmission-mcp .
```

Start the server (requires `config.toml` in the current directory):

```bash
docker compose up
```

---

## Running Tests

### Unit tests

```bash
uv run pytest tests/unit/
```

### Integration tests

Requires Docker with either the modern Compose plugin (`docker compose`) or the
legacy standalone binary (`docker-compose`). The harness auto-detects which is
available at startup and fails fast with a clear message if neither is found.

The harness automatically starts and stops a Transmission container
(`docker-compose.test.yml`) for the duration of the test session.

```bash
uv run pytest tests/integration/
```

#### Optional environment variables

| Variable | Default | Purpose |
|---|---|---|
| `TRANSMISSION_TEST_HOST` | `localhost` | Transmission RPC host |
| `TRANSMISSION_TEST_PORT` | `19091` | Transmission RPC port |
| `TRANSMISSION_TEST_USERNAME` | _(none)_ | RPC username, if auth is enabled |
| `TRANSMISSION_TEST_PASSWORD` | _(none)_ | RPC password, if auth is enabled |
| `TRANSMISSION_TEST_TIMEOUT_SECONDS` | `120` | Seconds to wait for container readiness |

### All tests

```bash
uv run pytest
```

### Docker build and compose

Verifies that the `Dockerfile` builds successfully and that `docker compose up` starts the server. Cleans up after itself.

```bash
bash scripts/test-docker.sh
```

---

## Managing Dependencies

### Add a runtime dependency

```bash
uv add <package>
```

### Add a dev dependency

```bash
uv add --dev <package>
```

### Upgrade all dependencies

```bash
uv lock --upgrade
```
