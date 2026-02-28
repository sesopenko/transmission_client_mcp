# Requirements Clarification Questions

Three items from your initial answers need clarification before I can proceed.

---

## Clarification 1 — Question 6 (MCP Server Framework)

**Context**: Your answer mentioned `transmission-rpc` (the library for talking to Transmission). That's confirmed and noted. However, Q6 was asking about a *different* concern: the framework that implements the **MCP protocol itself** — the part that speaks to LibreChat over HTTP/SSE.

These are two separate libraries in the project:

| Layer | Purpose | Your choice so far |
|---|---|---|
| Transmission client | Talks to Transmission's RPC API | `transmission-rpc==7.0.11` (confirmed) |
| MCP server framework | Implements MCP protocol, exposes HTTP/SSE server for LibreChat | **still needed** |

Which MCP server framework should be used?

A) `mcp` — the official Python MCP SDK (`pip install mcp`). Maintained by Anthropic/modelcontextprotocol. Supports HTTP/SSE transport. This is the standard choice for Python MCP servers.
B) `fastmcp` — a higher-level wrapper around the official `mcp` SDK with less boilerplate
C) Build without a framework — implement the MCP HTTP/SSE protocol manually
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Clarification 2 — Question 7 (Package Management)

**Context**: You selected A (`pyproject.toml` with `uv`) but noted you're new to `uv` and more comfortable with `pip-compile`. Since you picked A, I want to confirm your intent:

`uv` conceptually maps to your existing pip-compile workflow like this:

| pip-compile flow | uv equivalent |
|---|---|
| `requirements.in` | `pyproject.toml` `[project.dependencies]` |
| `pip-compile requirements.in -o requirements.txt` | `uv lock` (generates `uv.lock`) |
| `pip install -r requirements.txt` | `uv sync` |
| `pip-compile --upgrade ...` | `uv lock --upgrade` |
| Run app in venv | `uv run python ...` (manages venv automatically) |

`uv` is faster and simpler in practice — it's one tool instead of pip + pip-compile + virtualenv. However, if you prefer the familiar `pip-compile` workflow, that's a valid choice too.

Which would you prefer?

A) Use `uv` with `pyproject.toml` — I'll learn it, and I appreciate the simpler workflow comparison above
B) Use `pip-compile` with `requirements.in` / `requirements.txt` — stick with what I know
X) Other (please describe after [Answer]: tag below)

[Answer]: X

I'd like to use uv t finally get some experience in it.  Include instructions for common developer commands in MAINTAINERS.md.  I can work with an LLM to sort through learnings.

---

## Clarification 3 — Question 11 (Security Extension — Explanation)

**Context**: You asked for more explanation. Here it is:

The security extension adds a set of **15 automated compliance rules** (SECURITY-01 through SECURITY-15) that I check at each stage of the workflow. If any rule is violated, I **block** the stage and require you to approve a fix before continuing.

**What the rules cover:**

| Rule | Topic | Applies to this project? |
|---|---|---|
| SECURITY-01 | Encryption at rest/transit for databases | Likely N/A (no database in this project) |
| SECURITY-02 | Access logging on load balancers/API gateways | Likely N/A (simple LAN server) |
| SECURITY-03 | Structured application logging (no secrets in logs) | YES — relevant |
| SECURITY-04 | HTTP security headers (CSP, HSTS, etc.) | Partially — LAN-only, low risk |
| SECURITY-05 | Input validation on all API parameters | YES — relevant |
| SECURITY-06 | Least-privilege IAM policies | N/A (no cloud IAM) |
| SECURITY-07 | Restrictive network/firewall rules | N/A (LAN tool, not cloud infra) |
| SECURITY-08 | Application-level access control (auth, CORS) | YES — LibreChat needs auth |
| SECURITY-09 | No default credentials, no stack traces in errors | YES — relevant |
| SECURITY-10 | Dependency pinning, vulnerability scanning, SBOM | YES — relevant |
| SECURITY-11 | Rate limiting, separation of security logic | Partially — LAN tool |
| SECURITY-12 | Password hashing, session management, MFA | Partially — depends on auth approach |
| SECURITY-13 | Safe deserialization, artifact integrity | Partially — relevant |
| SECURITY-14 | Security alerting, log retention (90 days min) | Likely N/A (home LAN tool) |
| SECURITY-15 | Exception handling, fail-closed errors | YES — relevant |

**In plain terms**: This is a LAN tool for home use, not a public internet service. About half the rules will be marked N/A automatically. The ones that DO apply (SECURITY-03, -05, -08, -09, -10, -15) are mostly good coding practices regardless.

**Choosing Yes**: I enforce the applicable rules as blocking constraints. This means better code quality but may slow things down if I flag issues.

**Choosing No**: I skip all security checks. Faster to build, appropriate for a personal/experimental tool.

Which do you choose?

A) Yes — enforce applicable security rules (good practices, will block on violations)
B) No — skip security rules (faster, appropriate for a personal LAN tool)
X) Other (please describe after [Answer]: tag below)

[Answer]: No, this is a personal LAN tool.  This will be used for people with home servers, home labs, etc.
