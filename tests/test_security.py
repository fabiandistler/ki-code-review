from ki_review.models import FileDiff, Finding, Severity
from ki_review.security import check_security


def test_check_security_reports_formatted_sql_with_source_line() -> None:
    files = [
        FileDiff(
            path="src/database.py",
            patch="",
            added_lines=(
                (
                    12,
                    "cursor.execute(f'SELECT * FROM users WHERE email = {email}')",
                ),
            ),
        )
    ]

    findings = check_security(files)

    assert findings == [
        Finding(
            code="SEC001",
            message="SQL query is built with string formatting.",
            severity=Severity.HIGH,
            path="src/database.py",
            line=12,
        )
    ]


def test_check_security_reports_hardcoded_tokens() -> None:
    files = [
        FileDiff(
            path="src/settings.py",
            patch="",
            added_lines=((8, 'GITHUB_TOKEN = "ghp_0123456789abcdef"'),),
        )
    ]

    findings = check_security(files)

    assert findings == [
        Finding(
            code="SEC002",
            message="A secret is hard-coded in source code.",
            severity=Severity.HIGH,
            path="src/settings.py",
            line=8,
        )
    ]


def test_check_security_reports_unsafe_defaults() -> None:
    files = [
        FileDiff(
            path="src/server.py",
            patch="",
            added_lines=(
                (21, "requests.get(url, verify=False)"),
                (22, "app.run(debug=True)"),
            ),
        )
    ]

    findings = check_security(files)

    assert findings == [
        Finding(
            code="SEC003",
            message="An unsafe security default is enabled.",
            severity=Severity.HIGH,
            path="src/server.py",
            line=21,
        ),
        Finding(
            code="SEC004",
            message="Network request is missing a timeout.",
            severity=Severity.MEDIUM,
            path="src/server.py",
            line=21,
        ),
        Finding(
            code="SEC003",
            message="An unsafe security default is enabled.",
            severity=Severity.HIGH,
            path="src/server.py",
            line=22,
        ),
    ]


def test_check_security_reports_network_calls_without_timeouts() -> None:
    files = [
        FileDiff(
            path="src/github.py",
            patch="",
            added_lines=(
                (5, "urlopen(request)"),
                (6, "requests.get(url, timeout=10)"),
            ),
        )
    ]

    findings = check_security(files)

    assert findings == [
        Finding(
            code="SEC004",
            message="Network request is missing a timeout.",
            severity=Severity.MEDIUM,
            path="src/github.py",
            line=5,
        )
    ]


def test_check_security_checks_multiline_request_timeouts() -> None:
    files = [
        FileDiff(
            path="src/client.py",
            patch="",
            added_lines=(
                (20, "response = requests.get("),
                (21, "    url,"),
                (22, "    timeout=5,"),
                (23, ")"),
                (30, "response = httpx.post("),
                (31, "    url,"),
                (32, ")"),
            ),
        )
    ]

    findings = check_security(files)

    assert findings == [
        Finding(
            code="SEC004",
            message="Network request is missing a timeout.",
            severity=Severity.MEDIUM,
            path="src/client.py",
            line=30,
        )
    ]


def test_check_security_detects_sql_format_methods_but_allows_parameters() -> None:
    files = [
        FileDiff(
            path="src/database.py",
            patch="",
            added_lines=(
                (
                    5,
                    'cursor.execute("SELECT id={}".format(user_id))',
                ),
                (6, 'cursor.execute("SELECT id=%s" % user_id)'),
                (
                    7,
                    'cursor.execute("SELECT id=%s", (user_id,))',
                ),
            ),
        )
    ]

    findings = check_security(files)

    assert findings == [
        Finding(
            code="SEC001",
            message="SQL query is built with string formatting.",
            severity=Severity.HIGH,
            path="src/database.py",
            line=5,
        ),
        Finding(
            code="SEC001",
            message="SQL query is built with string formatting.",
            severity=Severity.HIGH,
            path="src/database.py",
            line=6,
        ),
    ]
