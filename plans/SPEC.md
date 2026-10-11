---
language: python
target: http-service
created: 2026-10-11
---

## Goal

An interactive, graphical tool that reviews AI-generated code (e.g. pull requests) against best practices, showing diffs with severity-rated, clickable findings in the browser.

## Users

Solo developer (Fabian) reviewing his own AI-assisted PRs before push. Invocation: open the web UI on `localhost:8000`, paste a GitHub PR URL or a unified diff, get an HTML report with diff plus findings sorted by severity, each finding links to file and line.

## Non-goals

- No auto-fix and no auto-commit without a human.
- No replacement for human approval or security audit.
- No shell completion, no distro packaging.
- Target non-goal: TLS, auth, horizontal scaling.

## Assumptions

User confirmed all four defaults verbatim with "ja alles ok" (2026-10-11):

1. Users + invoke: "Solo-Dev (du), Browser-UI auf `localhost:8000`, PR-URL reinkleben oder Diff pasten?"
2. Non-goals: "Kein Auto-Fix/Commit, kein Ersatz für Human-Approval — ok?"
3. Data/secrets/external: "GitHub-API für Diffs (Token nur bei privaten Repos), sonst keine Secrets/DB — ok? LLM-Key nötig oder rein statisch?" — decided: purely static checks first, no LLM key required; GitHub fetch optional via `fetch_pr_diff`, public PRs work without token, private PRs accept a `GITHUB_TOKEN` env var at runtime only, never stored.
4. Done beyond smoke: "1 PR einfügen → HTML mit Diff + Findings (Severity, Datei:Zeile klickbar) in <2 Min — ok?"

Additional agreements:

- Language fixed to `python` (TypeScript requested but out of scope for this loop); framework `FastAPI` per deploy-targets.
- Target chosen by agent as `http-service` after user delegated ("target musste selber gucken was gut passt"); validated by software-architect subagent: only a browser UI satisfies "interaktiv und grafisch".
- Input priority: PR URL first, diff paste as fallback. Single page, no login. No PR size limit for PoC; performance note only.

## Definition of Done

Target `http-service` (from references/deploy-targets.md):

- Smoke command: `docker build -t app:test . && docker run --rm -d -p 8000:8000 --name t app:test && sleep 2 && curl -sf localhost:8000/health && docker rm -f t`
- Required artefact: `Dockerfile` (multi-stage, `--target test` runs suite), `/health` endpoint
- Non-goal: TLS, auth, horizontal scaling

User's done beyond smoke:

- Paste 1 PR (URL or diff) into the UI and get back HTML with the diff plus findings (severity, file:line clickable) in under 2 minutes locally.
