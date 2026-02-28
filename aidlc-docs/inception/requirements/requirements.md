# Requirements Document

## Intent Analysis

- **User Request**: Build a Python MCP server that exposes Transmission BitTorrent client controls as MCP tools for LibreChat
- **Request Type**: New Project (Greenfield)
- **Scope Estimate**: Single Component
- **Complexity Estimate**: Moderate — MCP server + Transmission integration + HTTP transport + config + tests

---

## Project Overview

An MCP (Model Context Protocol) server written in Python that wraps the Transmission BitTorrent client's RPC API and exposes torrent management operations as MCP tools. LibreChat (running on the LAN) will connect to this server over HTTP/SSE to allow AI assistants to manage torrents on behalf of the user.

**Target audience**: Home server and home lab users.

---

## Functional Requirements

### FR-01: MCP Server
- The project SHALL be an MCP server (not a library or CLI)
- The server SHALL expose Transmission torrent management as MCP tools
- The server SHALL use **FastMCP** as the MCP server framework
- The server SHALL communicate with Transmission via the **Transmission RPC HTTP API** using the `transmission-rpc==7.0.11` library

### FR-02: MCP Tools (Core Operations)
The server SHALL expose the following MCP tools:

| Tool | Description |
|---|---|
| `add_torrent` | Add a torrent by magnet link or HTTP/HTTPS URL; optional download directory override |
| `remove_torrent` | Remove a torrent (keeps downloaded data) |
| `remove_torrent_and_delete_data` | Remove a torrent and permanently delete all downloaded data |
| `start_torrent` | Start/resume a torrent |
| `stop_torrent` | Stop/pause a torrent |
| `list_torrents` | List all torrents sorted by date added (oldest first); returns a structured entry per torrent |
| `get_torrent` | Fetch detailed information for a single torrent by name |

### FR-02a: get_torrent Detail

**Lookup method: case-insensitive exact name match**

Rationale: LLMs naturally work with names, not opaque numeric IDs. An LLM calling `list_torrents` receives torrent names directly and can pass them to `get_torrent` without needing to track internal IDs across conversation turns. Exact matching avoids false ambiguity from partial matches; case-insensitivity reduces fragility from minor capitalisation differences.

**Returned fields:**

All fields from `list_torrents` for the matched torrent, plus:

| Field | Format | Notes |
|---|---|---|
| `save_path` | string | Full path where torrent files are saved |
| `ratio` | string | Upload/download ratio (e.g. "1.24") |
| `files` | list | One entry per file: name, size (human-readable), progress % |
| `error_message` | string or null | Error string if torrent is in an error state (e.g. "Blacklisted client, update or change client"); null otherwise |

**No-match behaviour:**
- If no torrent matches the name, return an error: `"No torrent found matching '[name]'"`

**Duplicate name behaviour:**

Rationale: True duplicates (same name, differing only in case) are rare but possible. Since numeric IDs are not exposed to the LLM, there is no mechanism to disambiguate programmatically. Returning an error with distinguishing details allows the LLM to relay the situation clearly to the user.

- If more than one torrent matches the name (case-insensitively), return an error listing each match with its `added_on` date and `size` so the user can identify which is which

### FR-02b: add_torrent Detail

**Accepted inputs:**
- Magnet links (`magnet:?xt=...`)
- HTTP/HTTPS URLs pointing to a `.torrent` file
- Local file paths are NOT supported

**Input validation:**
- The tool SHALL perform basic format validation before sending to Transmission
- A magnet link must be well-formed: `magnet:` scheme with at least one `xt` parameter containing a valid URN (e.g. `xt=urn:btih:...`)
- A URL must match `http://` or `https://` scheme and be well-formed; the path and content are not inspected (no check for `.torrent` extension or content type)
- Invalid inputs SHALL return a clear error message without contacting Transmission

**Download directory:**
- An optional `download_dir` parameter MAY be provided to override the save location
- If `transmission-rpc` supports fetching the session's default download directory, the tool SHALL enforce that any provided `download_dir` is within that default directory (path prefix check)
- Paths outside the default download directory SHALL be rejected with a clear error message
- Example: if default is `/downloads`, then `/downloads/movies` is allowed but `/tmp/files` is not
- If `transmission-rpc` does not support fetching the default directory, the path sandbox check SHALL be skipped and any path accepted

**Start behaviour:**
- If `transmission-rpc` exposes Transmission's "start when added" session setting, the tool SHALL respect it (defers to Transmission's configured default)
- If that setting is not accessible via the library, the torrent SHALL be started immediately on add

**Success response:**
- For HTTP/HTTPS URL inputs: return confirmation message plus torrent name, status, and size (once Transmission has resolved them)
- For magnet link inputs: return a simple confirmation message only (e.g. "Torrent added successfully") — magnet links require peer discovery before metadata is available

**Duplicate handling:**
- If the same torrent is added twice, silently succeed — Transmission rejects duplicates internally and the error will be passed through per FR-05 if needed

### FR-02b: list_torrents Detail
Each entry returned by `list_torrents` SHALL include the following fields:

| Field | Format | Notes |
|---|---|---|
| `added_on` | ISO 8601 datetime | Date the torrent was added |
| `name` | string | Torrent name |
| `size` | string | Total size (human-readable, e.g. "4.2 GB") |
| `progress` | string | Percentage complete (e.g. "73.5%") |
| `status` | string | e.g. "downloading", "seeding", "stopped", "checking" |
| `seeds` | string | Connected/total (e.g. "4/12") |
| `peers` | string | Connected/total (e.g. "2/8") |
| `download_speed` | string | In MB/s (e.g. "3.2 MB/s"); "0 MB/s" when not active |
| `upload_speed` | string | In MB/s (e.g. "1.1 MB/s"); "0 MB/s" when not active |
| `eta` | string | Formatted as HH:MM:SS; "N/A" when not applicable |

**Behaviour:**
- Results SHALL be sorted by date added, oldest first (FIFO order)
- No filtering or search parameters — always returns all torrents
- No pagination — always returns the full list
- When there are no torrents, return an empty list with the message "No torrents found"

### FR-03: HTTP/SSE Transport
- The server SHALL expose an HTTP/SSE endpoint (not stdio)
- The server SHALL support HTTP only — TLS/HTTPS is explicitly out of scope
- HTTPS termination is the responsibility of a reverse proxy (e.g. Traefik, Apache, nginx) in front of this server
- The server SHALL be accessible on the LAN by LibreChat
- The server SHALL be configurable for host and port binding

### FR-04: Configuration File
- The server SHALL read connection settings from a TOML config file
- The config file SHALL contain: Transmission host, port, username, password
- The config file SHALL contain: MCP server bind host and port
- The config file path SHALL be configurable (default: `config.toml` in working directory)
- Example structure:
  ```toml
  [transmission]
  host = "localhost"
  port = 9091
  username = "transmission"
  password = "password"

  [server]
  host = "0.0.0.0"
  port = 8080

  [logging]
  level = "info"
  ```

### FR-05: Error Handling
- Transmission error messages SHALL be passed through to the MCP client (AI assistant) verbatim
- This enables the AI to diagnose and report issues accurately to the user

### FR-06: Testing
- Tests SHALL use `pytest`
- **Unit tests**: SHALL be written continuously during each construction phase alongside the code being built — not delivered after construction is complete
- **Unit tests**: SHALL mock all `transmission-rpc` calls to test tool logic in isolation
- **Passing tests are a gate**: a construction phase SHALL NOT be considered complete unless all unit tests are passing; failing tests are a blocker
- **Integration tests**: SHALL test against a real Transmission instance (Docker-based)
- **Integration test setup is high risk**: the Docker-based Transmission integration test harness SHALL be established early in the project due to unknown feasibility and complexity — it is a priority to de-risk before building tool implementations
- **Deferred dependency**: integration tests that exercise `add_torrent` require a small, well-seeded public torrent URL (e.g. a tiny Linux distribution ISO); this URL SHALL be identified and supplied at the phase where that test functionality is built

### FR-07: Developer Documentation
- A `MAINTAINERS.md` file SHALL be included with common developer commands using `uv`
- The file SHALL cover: setup, running the server, running tests, adding dependencies, upgrading dependencies

---

## Non-Functional Requirements

### NFR-01: Language and Runtime
- Python 3.13+ (matches Debian 13 default)

### NFR-02: Package Management
- `uv` with `pyproject.toml` for dependency management
- `uv.lock` SHALL be committed to version control (pins all transitive dependencies)

### NFR-03: Key Dependencies
| Package | Version | Purpose |
|---|---|---|
| `fastmcp` | latest | MCP server framework (HTTP/SSE transport) |
| `transmission-rpc` | 7.0.11 | Transmission RPC client |
| `tomli` or stdlib `tomllib` | stdlib (3.11+) | TOML config parsing |
| `pytest` | latest | Test runner |
| `pytest-asyncio` | latest | Async test support |

**Note**: `tomllib` is built into Python 3.11+ stdlib, no extra dependency needed.

### NFR-04: Docker Deployment
- A `docker-compose.yml` SHALL be provided to run the MCP server
- The Docker Compose stack SHALL contain the MCP server only — Transmission is NOT included
- Transmission is an external dependency assumed to already be running on the user's network; it is only run in Docker for testing purposes
- A `Dockerfile` SHALL be provided for building the MCP server image

### NFR-05: Deployment Context
- LAN-only deployment (home server / home lab)
- Not internet-facing
- No cloud infrastructure or IAM requirements

### NFR-07: Logging
- The server SHALL log to stdout (console)
- A structured logging system SHALL be implemented where every log entry includes:
  - `severity` — one of: `trace`, `debug`, `info`, `warning`, `error`, `critical`
  - `message` — human-readable description
  - `metadata` — optional key/value pairs providing structured context (e.g. tool name, torrent name, result summary)
- The log level SHALL be configurable in `config.toml` under a `[logging]` section; entries below the configured level SHALL be suppressed
- Every tool invocation SHALL be logged at `info` level, including the tool name and relevant input parameters
- Tool return values SHALL be logged at `debug` level with rudimentary details (e.g. number of torrents returned, torrent name added)
- Errors from Transmission SHALL be logged at `error` level including the raw error message
- Example config:
  ```toml
  [logging]
  level = "info"
  ```

### NFR-09: Security Extension
- **Disabled** — this is a personal LAN tool; security rules are not enforced as blocking constraints

---

## Out of Scope

- Tracker management, peer info, file priority control (future expansion)
- Session settings management
- CLI interface
- Web UI
- Authentication on the MCP HTTP endpoint (LAN trust model)
- TLS/HTTPS termination (handled by reverse proxy)
- SBOM / vulnerability scanning pipeline

---

## Assumptions

- Transmission daemon is already running and accessible on the network
- LibreChat is configured to connect to the MCP server's HTTP/SSE endpoint
- The user understands `uv` basics (or will use MAINTAINERS.md as reference)
