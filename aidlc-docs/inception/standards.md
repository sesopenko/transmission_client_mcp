# Development & Code Quality Standards

Derived from `standards-questions.md` answers.
These standards are enforced from Phase 1 — before any Python source code is written.

---

## Tooling Summary

| Concern | Tool | Enforcement |
|---|---|---|
| Formatting | Ruff format | Pre-commit hook (blocks commit) |
| Linting | Ruff | Pre-commit hook (blocks commit) |
| Import order | Ruff (isort rules) | Pre-commit hook (blocks commit) |
| Type checking | Mypy (standard mode) | Pre-commit hook (blocks commit) |
| Test runner | pytest | Manual / phase gate |
| Coverage | pytest-cov | Measured and reported; no threshold gate |

---

## S-01: Formatting

- **Tool**: Ruff format (Black-compatible)
- All Python source files must be formatted before commit
- Enforced by pre-commit hook; unformatted commits are blocked
- Configuration lives in `pyproject.toml` under `[tool.ruff.format]`

---

## S-02: Linting

- **Tool**: Ruff
- Enabled rule sets (configured in `pyproject.toml` under `[tool.ruff.lint]`):
  - `E`, `W` — pycodestyle errors and warnings
  - `F` — pyflakes (undefined names, unused imports)
  - `I` — isort (import ordering)
  - `UP` — pyupgrade (modernise syntax)
  - `B` — flake8-bugbear (likely bugs and design issues)
- Lint failures block commits via pre-commit hook

---

## S-03: Import Organisation

- **Tool**: Ruff isort rules (rule set `I`)
- Grouping order: stdlib → third-party → local
- Alphabetical within each group
- Enforced automatically by the Ruff pre-commit hook

---

## S-04: Line Length

- **Maximum**: 120 characters
- Configured in both `[tool.ruff]` and `[tool.ruff.format]` in `pyproject.toml`
- Applies to all Python source and test files

---

## S-05: Type Annotations

- **Required on**: all public functions, methods, and class definitions
  - "Public" means not prefixed with `_`
  - Parameters, return types, and class-level attributes must be annotated
- Internal/private helpers are exempt but annotations are encouraged
- Unannotated public API surfaces are caught by Mypy

---

## S-06: Static Type Checking

- **Tool**: Mypy, standard mode
- Configuration in `pyproject.toml` under `[tool.mypy]`
- Mypy runs as part of the pre-commit hook; type errors block commits
- `Any` is permitted where genuinely necessary but should be rare

---

## S-07: Docstrings

- **Required on**: all public functions, classes, and methods
- **Format**: Google style
- **Principle**: write for users, not implementers
  - Describe *what* the function does, its inputs, outputs, and guarantees
  - Do not expose internal logic, private helpers, or implementation details
  - Preserve encapsulation — explain behaviour and usage, not how it works internally
- Example:
  ```python
  def list_torrents() -> list[TorrentEntry]:
      """Return all torrents sorted by date added, oldest first.

      Returns:
          A list of TorrentEntry objects. Returns an empty list when no
          torrents are present.

      Raises:
          TransmissionError: If the Transmission RPC call fails.
      """
  ```

---

## S-08: Dead Code & Unused Symbols

- Unused imports and unused variables are **lint errors** (Ruff rule `F401`, `F841`)
- These block commits via the pre-commit hook
- No `# noqa` suppression without an explanatory comment

---

## S-09: Error Handling

- **Expected errors** (e.g. "torrent not found", "invalid input") — return a value (e.g. an error string, `None`, or a typed result)
- **Unexpected errors** (e.g. network failure, library exception) — raise an exception; catch at the MCP tool boundary and pass through verbatim per FR-05
- Do not swallow exceptions silently
- Do not use exceptions for normal control flow

---

## S-10: Named Constants

- Magic numbers and magic strings used as keys or sentinel values **should** be assigned to named constants
- Enforced by code convention and review; not an automated lint rule
- Inline literals are acceptable for single-use values that are self-evident from context (e.g. `timeout=30`)

---

## S-11: Function & Method Length

- **Soft guideline**: functions and methods should fit on one screen (~50 lines)
- Not enforced by linter; flagged during review
- Long functions are a signal to extract helpers, not a hard error

---

## S-12: Pre-commit Hook Configuration

All of the following run on every `git commit` and block the commit on failure:

1. Ruff format (auto-fix then re-check)
2. Ruff lint (no auto-fix on commit; developer fixes manually)
3. Mypy type check

Configuration file: `.pre-commit-config.yaml` in the project root.
`pre-commit` is a dev dependency managed via `uv`.

---

## S-13: Test Coverage

- Measured by `pytest-cov` on every test run
- No minimum threshold is enforced as a gate
- Coverage report is generated and reviewed; drops in coverage are a review concern, not an automated failure

---

## Tooling Setup Requirement

All tooling (Ruff, Mypy, pre-commit hooks) must be configured and operational **before any Python source code is written**. Phase 1 of construction is the enforcement point for this requirement.
