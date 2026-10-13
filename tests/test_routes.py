from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ki_review.app import create_app
from ki_review.github import GitHubNotFoundError, GitHubRateLimitError

_DIFF = (Path(__file__).parent / "fixtures" / "sample.diff").read_text()


def test_home_page_offers_pr_and_diff_inputs() -> None:
    response = TestClient(create_app()).get("/")

    assert response.status_code == 200
    assert 'name="pr_url"' in response.text
    assert 'name="diff"' in response.text


def test_submit_diff_displays_file_and_patch() -> None:
    response = TestClient(create_app()).post("/reviews", data={"diff": _DIFF})

    assert response.status_code == 200
    assert "src/example.py" in response.text
    assert "hello from the PR" in response.text
    assert "README.md" in response.text
    assert "A second changed file." in response.text


def test_submit_pr_fetches_diff_and_displays_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fetch_sample_diff(url: str) -> str:
        assert url == "https://github.com/owner/repo/pull/42"
        return _DIFF

    monkeypatch.setattr("ki_review.app.fetch_pr_diff", fetch_sample_diff)

    response = TestClient(create_app()).post(
        "/reviews", data={"pr_url": "https://github.com/owner/repo/pull/42"}
    )

    assert response.status_code == 200
    assert "src/example.py" in response.text


def test_submit_without_input_shows_error_and_keeps_form() -> None:
    response = TestClient(create_app()).post("/reviews", data={})

    assert response.status_code == 400
    assert "Paste a PR URL or a unified diff." in response.text
    assert 'name="pr_url"' in response.text


def test_submit_invalid_pr_url_shows_error() -> None:
    response = TestClient(create_app()).post(
        "/reviews", data={"pr_url": "https://example.com/pull/42"}
    )

    assert response.status_code == 400
    assert "valid GitHub pull request URL" in response.text


def test_submit_unavailable_pr_shows_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_pr(url: str) -> str:
        raise GitHubNotFoundError(404, "Not Found")

    monkeypatch.setattr("ki_review.app.fetch_pr_diff", missing_pr)

    response = TestClient(create_app()).post(
        "/reviews", data={"pr_url": "https://github.com/owner/repo/pull/42"}
    )

    assert response.status_code == 404
    assert "Could not find or access" in response.text


def test_submit_rate_limited_pr_shows_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def rate_limited_pr(url: str) -> str:
        raise GitHubRateLimitError(403, "Forbidden")

    monkeypatch.setattr("ki_review.app.fetch_pr_diff", rate_limited_pr)

    response = TestClient(create_app()).post(
        "/reviews", data={"pr_url": "https://github.com/owner/repo/pull/42"}
    )

    assert response.status_code == 429
    assert "GitHub rate limit reached" in response.text


def test_submit_malformed_diff_shows_error() -> None:
    response = TestClient(create_app()).post(
        "/reviews", data={"diff": "not a unified diff"}
    )

    assert response.status_code == 400
    assert "Unified diff has no file headers" in response.text
