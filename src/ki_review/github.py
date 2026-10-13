from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from ki_review.config import get_settings


class InvalidPullRequestURL(ValueError):
    """Raised when a URL is not a GitHub pull request URL."""


class GitHubHTTPError(Exception):
    """Raised when GitHub returns an unsuccessful HTTP response."""

    def __init__(self, status_code: int, reason: str) -> None:
        super().__init__(f"GitHub API returned HTTP {status_code}: {reason}")
        self.status_code = status_code


class GitHubNotFoundError(GitHubHTTPError):
    """Raised when the pull request cannot be found or accessed."""


class GitHubRateLimitError(GitHubHTTPError):
    """Raised when GitHub rejects the request because of a rate limit."""


def fetch_pr_diff(url: str) -> str:
    owner, repository, pull_number = _parse_pull_request_url(url)
    api_url = (
        "https://api.github.com/repos/"
        f"{quote(owner, safe='')}/{quote(repository, safe='')}/pulls/{pull_number}"
    )
    request = Request(
        api_url,
        headers={
            "Accept": "application/vnd.github.diff",
            "User-Agent": "ki-review",
            "X-GitHub-Api-Version": "2026-03-10",
        },
    )
    token = get_settings().github_token
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8")
    except HTTPError as error:
        if error.code == 404:
            raise GitHubNotFoundError(error.code, error.reason) from error
        if _is_rate_limit_error(error):
            raise GitHubRateLimitError(error.code, error.reason) from error
        raise GitHubHTTPError(error.code, error.reason) from error


def _parse_pull_request_url(url: str) -> tuple[str, str, str]:
    try:
        parsed_url = urlparse(url)
        port = parsed_url.port
    except ValueError as error:
        raise InvalidPullRequestURL("Invalid GitHub pull request URL") from error

    path_parts = parsed_url.path.strip("/").split("/")
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != "github.com"
        or parsed_url.username is not None
        or parsed_url.password is not None
        or port not in (None, 443)
        or len(path_parts) != 4
        or not path_parts[0]
        or not path_parts[1]
        or path_parts[2] != "pull"
        or not path_parts[3].isdecimal()
    ):
        raise InvalidPullRequestURL(
            "Expected https://github.com/OWNER/REPO/pull/NUMBER"
        )

    return path_parts[0], path_parts[1], path_parts[3]


def _is_rate_limit_error(error: HTTPError) -> bool:
    if error.code == 429:
        return True
    return (
        error.headers.get("X-RateLimit-Remaining") == "0"
        or error.headers.get("Retry-After") is not None
    )
