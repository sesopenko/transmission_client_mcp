# Development & Code Quality Standards — Questions

Answer each question by marking your choice(s) or writing a free-text response.
These answers will be used to define the project's enforced quality standards.

---

## Q1: Code Formatter

Which formatter should be applied to all Python source?

- [ ] A — **Ruff format** (fast, Ruff's built-in formatter; Black-compatible)
- [ ] B — **Black** (the original opinionated formatter)
- [ ] C — **No formatter** — style is enforced manually

**Answer**: A

---

## Q2: Linter

Which linter(s) should enforce code quality rules?

- [ ] A — **Ruff** (fast, covers pyflakes + pycodestyle + isort + many plugins in one tool)
- [ ] B — **Flake8** (classic; slower; plugin ecosystem)
- [ ] C — **Pylint** (strictest; high noise; slow)
- [ ] D — **Ruff + Pylint** (broad coverage, higher noise)
- [ ] E — **No linter**

**Answer**: A

---

## Q3: Type Annotations

What level of type annotation is required?

- [ ] A — **All functions and methods** — every parameter and return type annotated; unannotated code is a lint error
- [ ] B — **Public API only** — module-level functions and public class methods; internal helpers exempt
- [ ] C — **Best effort** — encouraged but not enforced
- [ ] D — **None** — no type annotation requirement

**Answer**: B

Also, a claude rule around documentation strings will need to be created in the .claude directory to ensure the following:

Write docstrings for users, not implementers: describe what the function does, its inputs, outputs, and guarantees, without exposing internal logic or private helpers.
Preserve encapsulation — explain behavior and usage clearly, not how it works internally.

---

## Q4: Static Type Checker

Should a static type checker be run as part of the quality gate?

- [ ] A — **Mypy, strict mode** (`--strict`; disallows `Any`, missing annotations are errors)
- [ ] B — **Mypy, standard mode** (catches obvious errors; some flexibility)
- [ ] C — **Pyright / Pylance** (faster; used by VS Code by default)
- [ ] D — **No static type checker**

**Answer**: B

---

## Q5: Docstrings

Are docstrings required, and if so in what format?

- [ ] A — **Required on all public functions, classes, and methods** — format: Google style
- [ ] B — **Required on all public functions, classes, and methods** — format: NumPy style
- [ ] C — **Required on all public functions, classes, and methods** — plain prose, no specific format
- [ ] D — **Required only where logic is non-obvious** — judgement call
- [ ] E — **Not required** — code should be self-documenting via naming and types

**Answer**: A

---

## Q6: Import Organisation

How should imports be ordered and grouped?

- [ ] A — **Enforced by Ruff (isort-compatible rules)** — stdlib / third-party / local, alphabetical within groups
- [ ] B — **Enforced by isort standalone**
- [ ] C — **PEP 8 convention, not automatically enforced**
- [ ] D — **No requirement**

**Answer**: A

---

## Q7: Line Length

What is the maximum line length?

- [ ] A — **88 characters** (Black / Ruff default)
- [ ] B — **79 characters** (PEP 8 default)
- [ ] C — **100 characters**
- [ ] D — **120 characters**
- [ ] X — Other (specify): ___

**Answer**: D

---

## Q8: Test Coverage

Is a minimum test coverage threshold enforced?

- [ ] A — **Yes — 90%+ overall** (measured by `pytest-cov`; below threshold fails the gate)
- [ ] B — **Yes — 80%+ overall**
- [ ] C — **Yes — 100% on core business logic modules only** (tools, config, logging)
- [ ] D — **No enforced threshold** — coverage is measured and reported but not a gate

**Answer**: D

---

## Q9: Pre-commit Hooks

Should quality checks run automatically on `git commit` via pre-commit hooks?

- [ ] A — **Yes** — formatter, linter, and type checker run on every commit; commit is blocked if any fail
- [ ] B — **Yes** — formatter only on commit; linter and type checker run manually / in CI
- [ ] C — **No** — all checks run manually or in CI only

**Answer**: A

---

## Q10: Dead Code & Unused Symbols

How should unused imports, variables, and unreachable code be treated?

- [ ] A — **Lint error** — unused imports and variables are always a hard failure
- [ ] B — **Lint warning** — flagged but do not block commits or gates
- [ ] C — **No enforcement** — developer responsibility

**Answer**: A

---

## Q11: Error Handling Style

How should errors be surfaced within the codebase (internal to tool implementations)?

- [ ] A — **Exceptions only** — raise exceptions for all error conditions; callers catch at the boundary
- [ ] B — **Return values for expected errors, exceptions for unexpected** — e.g. return `None` or a result type for "not found"; raise for truly unexpected failures
- [ ] C — **No standard** — each function decides

**Answer**: B

---

## Q12: Magic Numbers & Constants

How should hard-coded values (timeouts, limits, string literals used as keys, etc.) be managed?

- [ ] A — **Named constants required** — all magic numbers/strings must be assigned to a named constant; inline literals are a lint error
- [ ] B — **Named constants strongly preferred** — enforced by code review convention, not automated
- [ ] C — **No requirement**

**Answer**: B

---

## Q13: Function & Method Length

Is there a maximum function or method length guideline?

- [ ] A — **Hard limit enforced by linter** (e.g. max 50 lines per function)
- [ ] B — **Soft guideline** — functions should fit on one screen (~50 lines); flagged in review but not automated
- [ ] C — **No limit** — length is a design concern, not a quality gate

**Answer**: B

---

## Q14: Enforcement Point

Where are quality gates enforced? (select all that apply)

- [ ] A — **Pre-commit hook** (local, on every `git commit`)
- [ ] B — **CI pipeline** (runs on push / PR; blocks merge if failing)
- [ ] C — **Manual** — developer runs checks before committing; nothing automated

*Note: CI pipeline is not in scope per the requirements, but can be added as a future concern.*

**Answer**: A

---

## Q15: Anything Else?

Are there any other standards, conventions, or non-negotiables not covered above?
(e.g. specific naming conventions beyond PEP 8, forbidden patterns, preferred abstractions, etc.)

**Answer**:

This must be set up early in the project, before any python code is to be written.
