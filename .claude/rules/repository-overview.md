# Claude Code Instructions

## repository-overview.md

`repository-overview.md` is the Docker Hub overview for `sesopenko/transmission_client_mcp`.
It is automatically pushed to Docker Hub on every merge to `main`. Keep it accurate and user-facing
(Docker Hub visitors, not developers — no badges, no source-install instructions).

**When any of the following change, you MUST update `repository-overview.md` before the task is considered complete:**

- A new MCP tool is implemented — add a row to the **Available Tools** table
- The Docker Compose example changes (image name, port mapping, config path) — update the example block
- Configuration options change (new keys, changed defaults) — update the **Configuration** section; the config example must include a descriptive inline comment for every key
- The MCP endpoint path or port changes — update the **Connecting an AI Application** section
- A tool is added or its behaviour changes significantly — update the **Example System Prompt** section to keep the `<tool>` entries and `<guidelines>` accurate; use the existing prompt in the file as the reference for structure and tone

### Rules

- Keep the file user-facing: describe what things do, not how they work internally
- The configuration example must include a descriptive inline TOML comment (`# …`) on every key explaining its purpose
- The Docker Compose example must use the published image (`sesopenko/transmission_client_mcp:latest`), not a local build reference
- Do not add developer workflow steps, test instructions, or maintainer notes
- Do not add a tool row until the tool is implemented and its tests pass
- Do not remove rows for tools that have been implemented
- Do not rewrite the Example System Prompt from scratch; make the minimum edits needed to keep it accurate
