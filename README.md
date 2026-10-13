# ki-code-review

An interactive browser tool that makes GitHub pull request changes easy to inspect. Paste a pull request URL or a unified diff and read the file-by-file changes with line numbers in the browser.

## Run locally

Requires `uv`.

```sh
uv sync --locked
uv run python -m ki_review
```

Open `http://localhost:8000` in the browser:

1. Paste a GitHub pull request URL such as `https://github.com/owner/repo/pull/42`, or
2. Paste a unified diff into the diff form.

The page shows each changed path with its unified diff. Invalid URLs, unavailable PRs, rate limits, and malformed diffs return a readable HTML error while keeping the form.

## Private repositories

Public pull requests work without credentials. For private repositories, set `GITHUB_TOKEN` at runtime (never stored):

```sh
GITHUB_TOKEN=ghp_xxx uv run python -m ki_review
```

`HOST` and `PORT` are also read from the environment (`0.0.0.0` and `8000` by default).

## Docker

```sh
docker build --target runtime -t ki-review:smoke .
docker run --rm -p 8000:8000 --name ki-review ki-review:smoke
```

Then open `http://localhost:8000`. `GET /health` returns `{"status": "ok"}`.
