import sys

from ki_review.hallucinated import check_hallucinated_apis
from ki_review.models import FileDiff, Finding, Severity


def test_check_hallucinated_apis_reports_unknown_imports() -> None:
    files = [
        FileDiff(
            path="src/review.py",
            patch="",
            added_lines=(
                (3, "import json"),
                (4, "import ki_review_missing_package_8675309"),
            ),
        )
    ]

    findings = check_hallucinated_apis(files)

    assert findings == [
        Finding(
            code="API001",
            message=(
                "Imported module 'ki_review_missing_package_8675309' is unavailable "
                "in the current environment."
            ),
            severity=Severity.HIGH,
            path="src/review.py",
            line=4,
        )
    ]


def test_check_hallucinated_apis_respects_python_version_guards() -> None:
    major, minor = sys.version_info[:2]
    files = [
        FileDiff(
            path="src/compat.py",
            patch="",
            added_lines=(
                (10, f"if sys.version_info > ({major}, {minor}):"),
                (11, "    import ki_review_future_package_8675309"),
                (12, f"if sys.version_info <= ({major}, {minor}):"),
                (13, "    import ki_review_missing_package_8675309"),
            ),
        )
    ]

    findings = check_hallucinated_apis(files)

    assert findings == [
        Finding(
            code="API001",
            message=(
                "Imported module 'ki_review_missing_package_8675309' is unavailable "
                "in the current environment."
            ),
            severity=Severity.HIGH,
            path="src/compat.py",
            line=13,
        )
    ]


def test_check_hallucinated_apis_reports_removed_pandas_append() -> None:
    files = [
        FileDiff(
            path="src/data.py",
            patch="",
            added_lines=((27, "result = dataframe.append(other)"),),
        )
    ]

    findings = check_hallucinated_apis(files)

    assert findings == [
        Finding(
            code="API002",
            message=(
                "pandas DataFrame/Series.append was removed in pandas 2.0; "
                "use pandas.concat()."
            ),
            severity=Severity.HIGH,
            path="src/data.py",
            line=27,
        )
    ]
