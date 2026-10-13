import pytest

from ki_review.models import (
    FileDiff,
    Finding,
    ReviewReport,
    ReviewRequest,
    Severity,
    build_finding,
)


def test_build_finding_converts_severity_and_preserves_location() -> None:
    finding = build_finding(
        code="SEC001",
        message="Use a parameterized query.",
        severity="high",
        path="src/store.py",
        line=12,
    )

    assert finding == Finding(
        code="SEC001",
        message="Use a parameterized query.",
        severity=Severity.HIGH,
        path="src/store.py",
        line=12,
    )


def test_domain_models_represent_diff_request_and_report() -> None:
    file_diff = FileDiff(
        path="src/store.py",
        patch="@@ -1 +1 @@\n-old\n+new",
        added_lines=((1, "new"),),
    )
    request = ReviewRequest(diff="diff text")
    finding = build_finding("SEC001", "Use parameters.", "critical", file_diff.path, 1)
    report = ReviewReport(request=request, findings=[finding])

    assert file_diff.added_lines == ((1, "new"),)
    assert report.request is request
    assert report.findings == [finding]


def test_build_finding_rejects_unknown_severity() -> None:
    with pytest.raises(ValueError):
        build_finding("SEC001", "Use parameters.", "urgent", "src/store.py", 1)
