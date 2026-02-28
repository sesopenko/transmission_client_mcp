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

```bash
uv run python -m transmission_mcp
```

Pass `--config <path>` to use a non-default config file location.

---

## Running Tests

### Unit tests

```bash
uv run pytest tests/unit/
```

### Integration tests

Requires a running Transmission instance (see `docker-compose.test.yml`).

```bash
uv run pytest tests/integration/
```

### All tests

```bash
uv run pytest
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
