import asyncio
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from ki_review.diff import DiffParseError, parse_unified_diff
from ki_review.github import (
    GitHubHTTPError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    InvalidPullRequestURL,
    fetch_pr_diff,
)
from ki_review.ui import render_review_page


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    def home() -> HTMLResponse:
        return HTMLResponse(render_review_page())

    @app.post("/reviews", response_class=HTMLResponse)
    async def submit_review(request: Request) -> HTMLResponse:
        try:
            form_fields = parse_qs(
                (await request.body()).decode("utf-8"), keep_blank_values=True
            )
        except UnicodeDecodeError:
            return _review_error("Form data must be valid UTF-8.", 400)

        pr_url = form_fields.get("pr_url", [""])[0].strip()
        diff_text = form_fields.get("diff", [""])[0]
        if not pr_url and not diff_text:
            return _review_error("Paste a PR URL or a unified diff.", 400)
        if pr_url and diff_text:
            return _review_error(
                "Submit either a PR URL or a unified diff, not both.",
                400,
                pr_url=pr_url,
                diff_text=diff_text,
            )

        try:
            unified_diff = (
                await asyncio.to_thread(fetch_pr_diff, pr_url) if pr_url else diff_text
            )
            files = parse_unified_diff(unified_diff)
        except InvalidPullRequestURL:
            return _review_error(
                "Enter a valid GitHub pull request URL.", 400, pr_url=pr_url
            )
        except GitHubNotFoundError:
            return _review_error(
                "Could not find or access that GitHub pull request.",
                404,
                pr_url=pr_url,
            )
        except GitHubRateLimitError:
            return _review_error(
                "GitHub rate limit reached. Try again later or configure GITHUB_TOKEN.",
                429,
                pr_url=pr_url,
            )
        except GitHubHTTPError:
            return _review_error(
                "GitHub could not provide the pull request diff.", 502, pr_url=pr_url
            )
        except OSError:
            return _review_error(
                "Could not connect to GitHub. Check the connection and try again.",
                502,
                pr_url=pr_url,
            )
        except DiffParseError as error:
            return _review_error(str(error), 400, pr_url=pr_url, diff_text=diff_text)

        return HTMLResponse(render_review_page(files))

    return app


def _review_error(
    message: str,
    status_code: int,
    *,
    pr_url: str = "",
    diff_text: str = "",
) -> HTMLResponse:
    return HTMLResponse(
        render_review_page(
            error_message=message,
            pr_url=pr_url,
            diff_text=diff_text,
        ),
        status_code=status_code,
    )
