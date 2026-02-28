# Requirements Clarification Questions

Please answer the following questions by filling in the letter choice after each `[Answer]:` tag.
If none of the provided options match your needs, choose the last option (Other/X) and describe your preference after the tag.

Let me know when you're done.

---

## Question 1
What is the primary purpose of this project?

A) An MCP server that exposes Transmission BitTorrent client controls as MCP tools (so AI assistants like Claude can manage torrents)
B) A standalone Python library/SDK for communicating with the Transmission RPC API
C) A command-line interface (CLI) tool for interacting with Transmission
D) Both an MCP server and a reusable Python library
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
Which Transmission interface should be used to communicate with Transmission?

A) Transmission RPC (HTTP-based JSON RPC API — the standard remote control interface)
B) Transmission's Unix socket interface
C) Direct interaction with Transmission's config/torrent files
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
Which Transmission operations should the MCP server expose? (Select the scope)

A) Core torrent management only: add, remove, start, stop, list torrents
B) Core management plus status/info: add, remove, start, stop, list, get torrent details, get session stats
C) Comprehensive: everything in B plus settings management, peer info, tracker management, file priority control
D) Full feature parity with Transmission's RPC API (all available methods)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
How should the MCP server connect to Transmission? (Authentication and configuration)

A) Connection settings (host, port, username, password) provided via environment variables at server startup
B) Connection settings provided via a config file (e.g., `config.toml` or `config.json`)
C) Connection settings passed as MCP tool arguments on each call
D) Environment variables (primary) with optional config file override
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 5
What MCP transport mechanism should this server use?

A) stdio transport (standard for local MCP servers — server runs as a subprocess of the MCP client)
B) HTTP/SSE transport (network-accessible server)
C) Both stdio and HTTP/SSE (configurable at startup)
X) Other (please describe after [Answer]: tag below)

[Answer]: B

It will be LibreChat that will be using it as an mcp toolset which will access it over the network.  It will be HTTP, accessible on the LAN.

---

## Question 6
Which Python MCP SDK should be used?

A) `mcp` (the official Python MCP SDK from Anthropic/modelcontextprotocol)
B) A different library (please specify in Other)
C) Build without an MCP framework — implement the protocol directly
X) Other (please describe after [Answer]: tag below)

[Answer]:

This should already be extracted away by the client library `transmission-rpc` (lateste version is 7.0.11)

Documents here: https://transmission-rpc.readthedocs.io/en/stable/

Quickstart example from the docs:

```python
import requests

from transmission_rpc import Client

torrent_url = "https://github.com/trim21/transmission-rpc/raw/v4.1.0/tests/fixtures/iso.torrent"
c = Client(host="localhost", port=9091, username="transmission", password="password")
c.add_torrent(torrent_url)

########


c = Client(username="transmission", password="password")

torrent_url = "magnet:?xt=urn:btih:e84213a794f3ccd890382a54a64ca68b7e925433&dn=ubuntu-18.04.1-desktop-amd64.iso"
c.add_torrent(torrent_url)

########


c = Client(username="trim21", password="123456")

torrent_url = "https://github.com/trim21/transmission-rpc/raw/v4.1.0/tests/fixtures/iso.torrent"
r = requests.get(torrent_url)

# client will base64 the torrent content for you.
c.add_torrent(r.content)

# or use a file-like object
with open("a", "wb") as f:
    f.write(r.content)
with open("a", "rb") as f:
    c.add_torrent(f)
```

---

## Question 7
What Python package management / project structure should be used?

A) `pyproject.toml` with `uv` (modern, fast Python package manager)
B) `pyproject.toml` with `pip` / standard tooling
C) `setup.py` / `setup.cfg` (legacy)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

With a caveat: I'm new to `uv`.  This is the flow i'm used to using:

### My typical pip-compile flow
1. Add the package to requirements.in, for example:
```bash
echo "requests==2.32.3" >> requirements.in
```

2. Recompile requirements.txt:
```bash
pip-compile requirements.in -o requirements.txt
```

3. Install the updated, pinned dependencies:
```bash
pip install -r requirements.txt
```

### Upgrade existing dependencies
To refresh pins to the latest compatible versions:
```bash
pip-compile --upgrade requirements.in -o requirements.txt
pip install -r requirements.txt
```

I tried using uv once but I got very confused. I don't program with python at my dayjob so my python skills are limited.

---

## Question 8
What is the testing approach?

A) Unit tests only (mock Transmission API calls)
B) Unit tests plus integration tests (tests against a real or Docker-based Transmission instance)
C) Minimal testing — just enough to verify the MCP server starts and basic tools work
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 9
Should error handling expose Transmission error details to the MCP client?

A) Yes — pass through Transmission error messages to the AI assistant for better diagnosis
B) No — return generic error messages and log details internally
C) Configurable — a setting controls verbosity
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 10
What Python version should be targeted?

A) Python 3.12+ (latest stable)
B) Python 3.11+
C) Python 3.10+ (wider compatibility)
X) Other (please describe after [Answer]: tag below)

[Answer]: X

3.13+ is what's installed by default in Debian 13 (my dev environment) so that's what we'll go with.

---

## Question 11: Security Extensions
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)
B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)
X) Other (please describe after [Answer]: tag below)

[Answer]: Explain this further then re-ask.
