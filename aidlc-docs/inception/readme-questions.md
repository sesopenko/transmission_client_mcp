# README Q&A

Questions and answers to guide the content and scope of `README.md`.
Answers marked **[from requirements]** are derived from existing project documentation.
Answers marked **[needed]** require input from the developer.

---

## 1. What is this project?

**Q**: What one-sentence description should open the README?

**A [from requirements]**: A Python MCP server that exposes Transmission BitTorrent client controls as MCP tools, allowing AI assistants (e.g. LibreChat) to manage torrents over HTTP/SSE.

---

## 2. Who is the target audience?

**Q**: Who is expected to use and read this README?

**A [from requirements]**: Home server and home lab users who already run Transmission and want to connect it to an AI assistant via MCP.

---

## 3. What prerequisite knowledge should the README assume?

**Q**: Can the README assume the reader knows what MCP is? What about Docker? `uv`?

**A [needed]**: ___

Suggested default: assume the reader knows Docker but not necessarily MCP; include a one-line explanation of MCP and a link to the MCP spec or FastMCP docs. Assume the reader doesn't understand uv, has never used it before.

---

## 4. What are the prerequisites for running this project?

**Q**: What must already be installed/running before using this server?

**A [from requirements]**:
- Transmission daemon running and accessible on the LAN
- Docker (for Docker-based deployment)
- LibreChat (or another MCP-compatible client) configured to connect to the MCP server's HTTP/SSE endpoint
- `uv` (for running from source)

**Q**: Should the README link to or explain how to install any of these?

**A [needed]**: just uv, the rest are out of scope.

---

## 5. How should the quick-start be structured?

**Q**: Which deployment path should be primary in the quick-start — Docker Compose or running from source?

**A [needed]**:   both, side by side.

Options:
- A) Docker Compose first (most users just want to run it)
- B) Source first (`uv run ...`)
- C) Both, side by side

---

## 6. What config keys must the README document?

**Q**: Which `config.toml` sections and keys should be shown in the README?

**A [from requirements]**:
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

**Q**: Should the README document all valid log level values (`trace`, `debug`, `info`, `warning`, `error`, `critical`)?

**A [needed]**: no, that's just clutter.

---

## 7. Should the README list and describe the available MCP tools?

**Q**: Should the README include a table or description of the tools the server exposes?

**A [needed]**: yes.  but add the documentation as the tools are created, not up front.  Add a .claude/rules/ rule to ensure this happens during development.

Available tools (from requirements):

| Tool | Description |
|---|---|
| `list_torrents` | List all torrents sorted by date added (oldest first) |
| `get_torrent` | Fetch detailed info for a single torrent by name (case-insensitive) |
| `add_torrent` | Add a torrent by magnet link or HTTP/HTTPS `.torrent` URL |
| `start_torrent` | Start/resume a torrent by name |
| `stop_torrent` | Stop/pause a torrent by name |
| `remove_torrent` | Remove a torrent (keeps downloaded data) |
| `remove_torrent_and_delete_data` | Remove a torrent and permanently delete all data |

---

## 8. How should LibreChat integration be documented?

**Q**: Should the README include instructions for configuring LibreChat to connect to this server?

**A [needed]**: no, don't mention librechat in the README.md, that's a personal detail of what I am integrating it with.  Just give generalized instructions on how to integrate the MCP server, LLM app agnostic.

If yes: what is the MCP endpoint URL format (e.g. `http://<host>:<port>/sse`)?

---

## 9. Should the README mention TLS/HTTPS?

**Q**: The server is HTTP-only. Should the README mention that HTTPS termination is the responsibility of a reverse proxy (e.g. Traefik, nginx)?

**A [from requirements]**: Yes — HTTPS is out of scope for the server; reverse proxy is the recommended path.

**Q**: Should the README provide any guidance or example for setting up a reverse proxy?

**A [needed]**: mention that it's out of scope.

---

## 10. Should the README include a security note?

**Q**: The server has no authentication on its MCP endpoint (LAN trust model). Should the README warn users not to expose it to the internet?

**A [needed]**: yes

---

## 11. Should the README link to MAINTAINERS.md?

**Q**: MAINTAINERS.md covers developer commands (setup, testing, dependencies). Should the README reference it for contributors?

**A [needed]**: yes, and create MAINTAINERS.md.  I think I mentioned CONTRIBUTING.md in the past, maintain consistency.  From this point, it's MAINTAINERS.md.  Add a rule in .claude/rules/ to maintain this as commands change.  Don't document them all up front, document them as they're added (ie: when we get to integration testing).

---

## 12. Should the README include a license section?

**Q**: The project is licensed under GNU GPL v3. Should the README include a license badge or section?

**A [needed]**: yes.  And it's Copyright (c) Sean Esopenko 2026

---

## 13. Should the README include badges?

**Q**: Should the README include any badges (e.g. license, Python version, build status)?

**A [needed]**: license, python version.  nothing else.

---

## 14. What should the README title be?

**Q**: What heading should appear at the top of the README?

**A [needed]**: Transmission Client MCP

Suggestions:
- `transmission-client-mcp`
- `Transmission MCP Server`
- `Transmission BitTorrent MCP Server`

---

## Summary of items needing developer input

| # | Question | Default if no answer |
|---|---|---|
| 3 | Assumed reader knowledge of MCP/Docker/uv | Assume Docker known; explain MCP briefly |
| 4 | Link to Transmission/Docker/LibreChat install guides? | No links; just list prerequisites |
| 5 | Quick-start: Docker first or source first? | Docker Compose first |
| 6 | Document all log level values? | Yes, list them |
| 7 | Include MCP tools table? | Yes |
| 8 | LibreChat integration instructions? | Brief mention with endpoint URL format |
| 9 | Reverse proxy guidance? | Mention it; no detailed example |
| 10 | Security warning about LAN-only use? | Yes, one-line note |
| 11 | Link to MAINTAINERS.md? | Yes |
| 12 | License section? | Yes, one-line with link |
| 13 | Badges? | License badge only |
| 14 | README title? | `Transmission MCP Server` |
