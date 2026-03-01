# GitHub Actions — Requirements Q&A

Answer each question by replacing the `[ ]` placeholder with your answer or by ticking a checkbox.
Questions with multiple options use checkboxes; tick all that apply unless the question says "choose one".

---

## 1. Workflow triggers

**Which events should trigger the CI (build + test) workflow?**
*(choose all that apply)*

- [x] Push to `main`
- [ ] Push to any branch
- [x] Pull request targeting `main`
- [ ] Pull request targeting any branch
- [ ] Manual dispatch (`workflow_dispatch`)

---

## 2. Docker publish trigger

**When should the Docker image be published to DockerHub?**
*(choose one)*

- [x] On every push to `main` (continuous delivery)
- [ ] Only when a git tag matching `v*` is pushed (release-gated)
- [ ] Both: push a `latest` tag on every `main` merge, and a version tag on `v*` tags
- [ ] Other: ___

---

## 3. Docker image tagging strategy

**Which tags should be applied to the published image?**
*(choose all that apply)*

- [x] `latest` — always points to the most recently published build
- [ ] Git SHA (short) — e.g. `sha-a1b2c3d`
- [x] Semver from git tag — e.g. `1.2.3` and `1.2` and `1` (when a `v1.2.3` tag is pushed)
- [ ] Branch name — e.g. `main`
- [ ] Other: ___

---

## 4. DockerHub image name

**What is the full DockerHub image name?**

Format: `<username>/<repository>` — e.g. `sesopenko/transmission-mcp`

Answer: sesopenko/transmission_client_mcp

---

## 5. GitHub secret / variable names

You mentioned secrets and variables are already configured in the GitHub repo.

**What are the exact names of the DockerHub credentials stored in GitHub?**

| Credential | GitHub secret / variable name |
|---|--|
| DockerHub username | DOCKERHUB_USERNAME |
| DockerHub personal access token | DOCKERHUB_ACCESS_TOKEN |

*(Tip: secrets are under Settings → Secrets and variables → Actions)*

---

## 6. Test scope in CI

The project has unit tests (`tests/unit/`) and integration tests (`tests/integration/`).
Integration tests require a running Transmission container and use `docker-compose.test.yml`.

**Which tests should run in CI?**
*(choose one)*

- [ ] Unit tests only (faster, no Docker-in-Docker needed)
- [ ] Unit tests + integration tests (slower; requires Docker service in the runner)
- [x] All tests via `uv run pytest` (same as integration tests option above)

---

## 7. Code quality checks in CI

**Should the CI workflow enforce code quality gates before building?**
*(choose all that apply)*

- [x] `ruff format --check` — formatting
- [x] `ruff check` — linting
- [x] `mypy src/` — type checking
- [ ] None — quality is enforced locally via pre-commit hooks only

---

## 8. Target platforms for the Docker image

**Which CPU architectures should the image be built for?**
*(choose all that apply)*

- [x] `linux/amd64` (x86-64 — standard cloud/desktop)
- [ ] `linux/arm64` (e.g. Raspberry Pi 4/5, Apple Silicon servers, AWS Graviton)
- [ ] `linux/arm/v7` (older 32-bit ARM, e.g. Raspberry Pi 3)

---

## 9. Workflow structure

**Should CI (test) and CD (publish) be separate workflow files, or combined in one?**
*(choose one)*

- [x] Separate files — cleaner separation, publish job triggers after CI passes
- [ ] Single file — one workflow with sequential jobs (test → build → push)

---

## 10. Publish gate

**Should the Docker image only be published if all tests (and quality checks) pass?**
*(choose one)*

- [x] Yes — publish is blocked if any earlier job fails
- [ ] No — publish regardless (not recommended, but valid for some workflows)

---

## 11. Runner

**Which GitHub Actions runner should be used?**
*(choose one)*

- [x] `ubuntu-latest` (GitHub-hosted, free tier)
- [ ] Self-hosted runner
- [ ] Other: ___

---

## 12. Python version pin

The project requires Python ≥ 3.13 (`pyproject.toml`).

**Should CI pin to a specific Python 3.13 patch version, or use the latest 3.13.x?**
*(choose one)*

- [x] Latest `3.13.x` (always gets patch updates automatically)
- [ ] Pin to a specific version, e.g. `3.13.2`
- [ ] Match the Docker base image (`python:3.13-slim`) — use whatever version that resolves to

---
