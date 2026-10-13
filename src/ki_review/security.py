import re

from ki_review.models import FileDiff, Finding, build_finding

_SQL_EXECUTION = re.compile(r"\b(?:execute|executemany)\s*\(", re.IGNORECASE)
_SQL_STATEMENT = re.compile(
    r"\b(?:select|insert|update|delete|replace)\b", re.IGNORECASE
)
_SQL_FORMATTING = re.compile(r"\bf[\"']|\.format\s*\(|[\"'].*[\"']\s*%\s*[\w(]")
_SECRET_ASSIGNMENT = re.compile(
    r"\b[A-Za-z_]*(?:password|passwd|secret|api[_-]?key|token)\b"
    r"\s*[:=]\s*([\"'])(.*?)\1",
    re.IGNORECASE,
)
_SECRET_PLACEHOLDERS = {
    "changeme",
    "change-me",
    "dummy",
    "example",
    "placeholder",
    "replace-me",
    "test",
}
_UNSAFE_DEFAULT = re.compile(r"\b(?:verify\s*=\s*False|debug\s*=\s*True)\b")
_OUTBOUND_REQUEST = re.compile(
    r"\b(?:requests|httpx)\.(?:get|post|put|patch|delete|request)\s*\(|"
    r"\burlopen\s*\("
)
_REQUEST_TIMEOUT = re.compile(r"\btimeout\s*=")


def check_security(files: list[FileDiff]) -> list[Finding]:
    findings: list[Finding] = []
    for file_diff in files:
        for added_line_index, (line_number, added_line) in enumerate(
            file_diff.added_lines
        ):
            if (
                _SQL_EXECUTION.search(added_line)
                and _SQL_STATEMENT.search(added_line)
                and _SQL_FORMATTING.search(added_line)
            ):
                findings.append(
                    build_finding(
                        code="SEC001",
                        message="SQL query is built with string formatting.",
                        severity="high",
                        path=file_diff.path,
                        line=line_number,
                    )
                )
            secret_assignment = _SECRET_ASSIGNMENT.search(added_line)
            if secret_assignment is not None:
                secret_value = secret_assignment.group(2).strip().lower()
                if (
                    secret_value not in _SECRET_PLACEHOLDERS
                    and not secret_value.startswith(("your-", "your_"))
                ):
                    findings.append(
                        build_finding(
                            code="SEC002",
                            message="A secret is hard-coded in source code.",
                            severity="high",
                            path=file_diff.path,
                            line=line_number,
                        )
                    )
            if _UNSAFE_DEFAULT.search(added_line):
                findings.append(
                    build_finding(
                        code="SEC003",
                        message="An unsafe security default is enabled.",
                        severity="high",
                        path=file_diff.path,
                        line=line_number,
                    )
                )
            outbound_request = _OUTBOUND_REQUEST.search(added_line)
            if outbound_request and not _request_has_timeout(
                file_diff.added_lines, added_line_index, outbound_request
            ):
                findings.append(
                    build_finding(
                        code="SEC004",
                        message="Network request is missing a timeout.",
                        severity="medium",
                        path=file_diff.path,
                        line=line_number,
                    )
                )
    return findings


def _request_has_timeout(
    added_lines: tuple[tuple[int, str], ...],
    call_index: int,
    call_match: re.Match[str],
) -> bool:
    call_source: list[str] = []
    parenthesis_depth = 0
    previous_line_number: int | None = None

    for line_index in range(call_index, len(added_lines)):
        line_number, source_line = added_lines[line_index]
        if previous_line_number is not None and line_number != previous_line_number + 1:
            return False

        call_source.append(source_line)
        start_character = call_match.end() - 1 if line_index == call_index else 0
        quote: str | None = None
        escaped = False
        for character in source_line[start_character:]:
            if quote is not None:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == quote:
                    quote = None
            elif character in ("'", '"'):
                quote = character
            elif character == "(":
                parenthesis_depth += 1
            elif character == ")":
                parenthesis_depth -= 1
                if parenthesis_depth == 0:
                    return _REQUEST_TIMEOUT.search("\n".join(call_source)) is not None

        previous_line_number = line_number
    return False
