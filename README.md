# Transmission Client MCP

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE.txt)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/)
[![CI](https://github.com/sesopenko/transmission_client_mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sesopenko/transmission_client_mcp/actions/workflows/ci.yml)

An MCP server that exposes [Transmission](https://transmissionbt.com/) BitTorrent client controls as tools, allowing AI assistants to manage torrents on your behalf.

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/) is an open standard that lets AI assistants call external tools and services. This server implements MCP over HTTP/SSE so any MCP-compatible AI application can control your Transmission instance.

---

## Prerequisites

- **Transmission** — running and accessible on your network
- **Docker** — for the Docker Compose deployment path
- **uv** — for the source deployment path (see [Installing uv](https://docs.astral.sh/uv/getting-started/installation/))

---

## Quick Start

### Option A — Docker Compose

1. Create a `docker-compose.yml`:

   ```yaml
   services:
     transmission-mcp:
       image: sesopenko/transmission_client_mcp:latest
       ports:
         - "8080:8080"
       volumes:
         - ./config.toml:/config/config.toml:ro
       restart: unless-stopped
   ```

2. Copy the example config and edit it:

   ```bash
   cp config.toml.example config.toml
   ```

3. Start the server:

   ```bash
   docker compose up -d
   ```

### Option B — Run from Source

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already.

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Copy the example config and edit it:

   ```bash
   cp config.toml.example config.toml
   ```

4. Start the server:

   ```bash
   uv run python -m transmission_mcp
   ```

---

## Configuration

Create a `config.toml` in the working directory (or pass `--config <path>`):

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

---

## Connecting an AI Application

Point your MCP-compatible AI application at the server's MCP endpoint:

```
http://<host>:<port>/mcp
```

For example, if the server is running on `192.168.1.10` with the default port:

```
http://192.168.1.10:8080/mcp
```

Consult your AI application's documentation for how to register an MCP server.

---

## Example System Prompt

Copy and adapt this system prompt to give your AI assistant clear guidance on using the Transmission tools.

```xml
<system>
  <role>
    You are a home network download manager specialising in BitTorrent. Your
    expertise covers torrent lifecycle management — queuing, monitoring progress,
    organising downloads, and cleaning up completed or unwanted transfers. You
    have direct control of a Transmission instance via MCP tools.
  </role>
  <tools>
    <tool name="list_torrents">List all torrents, sorted by date added (oldest first).</tool>
    <tool name="add_torrent">Add a torrent by magnet link or HTTP/HTTPS URL.</tool>
    <tool name="get_torrent">Get detailed information about a torrent by name.</tool>
    <tool name="start_torrent">Start or resume a paused torrent by name.</tool>
    <tool name="stop_torrent">Stop or pause an active torrent by name.</tool>
    <tool name="remove_torrent">Remove a torrent by name, keeping data on disk.</tool>
    <tool name="remove_torrent_and_delete_data">Remove a torrent and permanently delete all downloaded data.</tool>
  </tools>
  <guidelines>
    <item>When the user asks about downloads, call list_torrents first for an overview, then get_torrent for details on a specific item.</item>
    <item>Before calling remove_torrent or remove_torrent_and_delete_data, confirm the torrent name with the user.</item>
    <item>Before calling remove_torrent_and_delete_data, explicitly warn the user that all downloaded data will be permanently deleted and require unambiguous confirmation before proceeding.</item>
    <item>Prefer stop_torrent over removal when the user only wants to pause activity.</item>
  </guidelines>
</system>
```

---

## Available Tools

| Tool | Description |
|---|---|
| `list_torrents` | List all torrents managed by Transmission, sorted by date added (oldest first). |
| `add_torrent` | Add a torrent by magnet link or HTTP/HTTPS URL, with an optional download directory override. |
| `get_torrent` | Fetch detailed information for a single torrent by name, including file list, save path, ratio, and error state. |
| `start_torrent` | Start or resume a paused torrent by name. |
| `stop_torrent` | Stop or pause an active torrent by name. |
| `remove_torrent` | Remove a torrent by name, keeping all downloaded data on disk. |
| `remove_torrent_and_delete_data` | Remove a torrent by name and permanently delete all downloaded data. |

> Tools are documented here as they are implemented.

---

## Security

This server has **no authentication** on its MCP endpoint. It is designed for LAN use only.

**Do not expose this server directly to the internet.**

If you need to access it remotely, place it behind a reverse proxy that handles TLS termination and access control. Configuring a reverse proxy is outside the scope of this project.

---

## Contributing / Maintaining

See [MAINTAINERS.md](MAINTAINERS.md) for setup, development commands, and how to run tests.

---

## License

Copyright (c) Sean Esopenko 2026

This project is licensed under the [GNU General Public License v3.0](LICENSE.txt).

---

## Acknowledgement: Riding on the Backs of Giants

This project was built with the assistance of [Claude Code](https://claude.ai/code), an AI coding assistant developed by Anthropic.

AI assistants like Claude are trained on enormous amounts of data — much of it written by the open-source community: the libraries, tools, documentation, and decades of shared knowledge that developers have contributed freely. Without that foundation, tools like this would not be possible.

In recognition of that debt, this project is released under the [GNU General Public License v3.0](LICENSE.txt). The GPL ensures that this code — and any derivative work — remains open source. It is a small act of reciprocity: giving back to the commons that made it possible.

To every developer who ever pushed a commit to a public repo, wrote a Stack Overflow answer, or published a package under an open license — thank you.
