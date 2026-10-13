from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class FileDiff:
    path: str
    patch: str
    added_lines: tuple[tuple[int, str], ...] = ()


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    severity: Severity
    path: str
    line: int


@dataclass(frozen=True)
class ReviewRequest:
    pr_url: str | None = None
    diff: str | None = None


@dataclass(frozen=True)
class ReviewReport:
    request: ReviewRequest
    findings: list[Finding]


def build_finding(
    code: str,
    message: str,
    severity: str,
    path: str,
    line: int,
) -> Finding:
    return Finding(
        code=code,
        message=message,
        severity=Severity(severity),
        path=path,
        line=line,
    )
