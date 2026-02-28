# Commit Message Guidelines — Questions

Answer each question by marking your choice or writing a free-text response.

---

## Q1: Convention

Which commit message convention should be followed?

- [ ] A — **Conventional Commits** (`type(scope): subject` — e.g. `feat(tools): add list_torrents`)
- [ ] B — **Free-form** — no enforced structure; descriptive prose subject line
- [ ] C — **Imperative subject line only** — e.g. "Add list_torrents tool"; no type prefix required
- [ ] X — Other (specify): ___

**Answer**: A

---

## Q2: Subject Line Length

What is the maximum length for the commit subject line (first line)?

- [ ] A — **50 characters** (Git/GitHub convention; fits in most log views)
- [ ] B — **72 characters** (common relaxed limit)
- [ ] C — **No hard limit** — keep it concise but don't count characters

**Answer**: A

---

## Q3: Subject Line Mood & Punctuation

- [ ] A — **Imperative mood, no trailing period** — "Add config loader", not "Added config loader."
- [ ] B — **Any tense, no trailing period**
- [ ] C — **No requirement**

**Answer**: A

---

## Q4: Commit Body

When is a commit body (lines after the blank line following the subject) required?

- [ ] A — **Always** — every commit must explain the why, not just the what
- [ ] B — **When the change is non-obvious** — required for anything beyond a trivial fix or rename
- [ ] C — **Never required** — subject line is sufficient; body is optional and used at the author's discretion

**Answer**: A

---

## Q5: Scope (if using Conventional Commits)

If Conventional Commits is chosen (Q1-A), should a scope be used?

- [ ] A — **Required** — every commit must include a scope (e.g. `feat(config):`, `fix(tools):`)
- [ ] B — **Optional** — include a scope when it adds clarity; omit when the change is cross-cutting
- [ ] C — **Never** — type only, no scope (e.g. `feat:`, `fix:`)
- [ ] N/A — Not using Conventional Commits

**Answer**: A

---

## Q6: Breaking Changes

How should breaking changes be marked?

- [ ] A — **Conventional Commits footer** — `BREAKING CHANGE: description` in the commit body footer
- [ ] B — **Subject line flag** — e.g. `feat!: remove stdio transport`
- [ ] C — **Both A and B** — `!` in subject plus `BREAKING CHANGE:` footer
- [ ] D — **Not applicable** — this project has no external API consumers

**Answer**: D

---

## Q7: WIP Commits

Are work-in-progress commits allowed on the main branch?

- [ ] A — **No** — every commit on main must be complete and passing all gates
- [ ] B — **Yes** — WIP commits are fine; clean up before tagging a release
- [ ] C — **Feature branches only** — WIP is allowed on branches; main must be clean

**Answer**: A

---

## Q8: Enforcement

Should commit message format be enforced automatically?

- [ ] A — **Yes — commitlint via pre-commit hook** (blocks non-conforming commits)
- [ ] B — **Yes — simple regex check via pre-commit hook** (e.g. check subject length and type prefix)
- [ ] C — **No — convention only**, enforced by review habit not tooling

**Answer**: A

---

## Q9: Anything Else?

Any other commit message rules not covered above?
(e.g. reference issue numbers, sign-off lines, emoji policy, co-author lines)

**Answer**:
