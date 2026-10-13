from email.message import Message
from io import BytesIO
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from ki_review.github import (
    GitHubNotFoundError,
    GitHubRateLimitError,
    InvalidPullRequestURL,
    fetch_pr_diff,
)


def test_fetch_pr_diff_uses_github_api_without_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request: Request | None = None

    def fake_urlopen(request: Request, timeout: float) -> BytesIO:
        nonlocal captured_request
        captured_request = request
        assert timeout == 10
        return BytesIO(b"diff --git a/file.py b/file.py\n")

    monkeypatch.setattr("ki_review.github.urlopen", fake_urlopen)

    diff = fetch_pr_diff("https://github.com/owner/repository/pull/42")

    assert diff == "diff --git a/file.py b/file.py\n"
    assert captured_request is not None
    assert (
        captured_request.full_url
        == "https://api.github.com/repos/owner/repository/pulls/42"
    )
    assert captured_request.get_header("Accept") == "application/vnd.github.diff"
    assert captured_request.get_header("Authorization") is None


def test_fetch_pr_diff_uses_github_token_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "private-repository-token")
    captured_request: Request | None = None

    def fake_urlopen(request: Request, timeout: float) -> BytesIO:
        nonlocal captured_request
        captured_request = request
        return BytesIO(b"private diff")

    monkeypatch.setattr("ki_review.github.urlopen", fake_urlopen)

    diff = fetch_pr_diff("https://github.com/owner/private-repository/pull/7")

    assert diff == "private diff"
    assert captured_request is not None
    assert (
        captured_request.get_header("Authorization")
        == "Bearer private-repository-token"
    )


def test_fetch_pr_diff_rejects_non_pull_request_urls() -> None:
    with pytest.raises(InvalidPullRequestURL):
        fetch_pr_diff("https://example.com/owner/repository/pull/7")


def test_fetch_pr_diff_maps_not_found_to_typed_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: Request, timeout: float) -> BytesIO:
        raise HTTPError(
            request.full_url,
            404,
            "Not Found",
            Message(),
            BytesIO(b"not found"),
        )

    monkeypatch.setattr("ki_review.github.urlopen", fake_urlopen)

    with pytest.raises(GitHubNotFoundError) as error:
        fetch_pr_diff("https://github.com/owner/repository/pull/7")

    assert error.value.status_code == 404


def test_fetch_pr_diff_maps_rate_limit_to_typed_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response_headers = Message()
    response_headers.add_header("X-RateLimit-Remaining", "0")

    def fake_urlopen(request: Request, timeout: float) -> BytesIO:
        raise HTTPError(
            request.full_url,
            403,
            "Forbidden",
            response_headers,
            BytesIO(b"rate limit exceeded"),
        )

    monkeypatch.setattr("ki_review.github.urlopen", fake_urlopen)

    with pytest.raises(GitHubRateLimitError) as error:
        fetch_pr_diff("https://github.com/owner/repository/pull/7")

    assert error.value.status_code == 403
