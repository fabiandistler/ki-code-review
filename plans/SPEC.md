---
language: python
target: http-service
created: 2026-10-11
---

## Goal

An interactive browser tool that makes GitHub pull request changes easy to inspect. Given a pull request URL or unified diff, it shows the file-by-file changes with file names and line numbers.

## Users

Solo developer (Fabian) inspecting pull requests before merging. Invocation: open the web UI on `localhost:8000`, paste a GitHub PR URL or unified diff, and read the changed files and line-by-line diff in the browser.

## Non-goals

- No automated code analysis, recommendations, severity ratings, or findings.
- No auto-fix and no auto-commit.
- No replacement for GitHub's review and approval workflow.
- No shell completion, no distro packaging.
- Target non-goal: TLS, auth, horizontal scaling.

## Assumptions

User clarified the product scope on 2026-10-13: the tool only visualizes pull request changes; it does not analyze code or generate findings.

1. Input: a GitHub pull request URL or pasted unified diff.
2. GitHub API provides pull request diffs; public pull requests work without a token, and private pull requests may use `GITHUB_TOKEN` at runtime. Never store the token.
3. No LLM key, database, or automated review checks are required.
4. Done beyond smoke: paste one PR URL or diff and see its changed files and line-by-line diff in the browser in under two minutes locally.

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

- Paste one PR URL or unified diff into the UI and see the changed files with line-by-line diffs in under two minutes locally.
