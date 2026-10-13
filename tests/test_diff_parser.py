import pytest

from ki_review.diff import DiffParseError, parse_unified_diff
from ki_review.models import FileDiff


def test_parse_unified_diff_tracks_added_lines_and_file_path() -> None:
    unified_diff = (
        "diff --git a/src/store.py b/src/store.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/src/store.py\n"
        "+++ b/src/store.py\n"
        "@@ -1,2 +1,3 @@\n"
        " SELECT 1\n"
        "-old()\n"
        "+new()\n"
        "+second()\n"
    )

    files = parse_unified_diff(unified_diff)

    assert files == [
        FileDiff(
            path="src/store.py",
            patch=unified_diff,
            added_lines=((2, "new()"), (3, "second()")),
        )
    ]


def test_parse_unified_diff_rejects_empty_input_with_typed_error() -> None:
    with pytest.raises(DiffParseError, match="empty"):
        parse_unified_diff("")


def test_parse_unified_diff_accepts_unprefixed_unified_patch() -> None:
    unified_diff = "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-old\n+new\n"

    files = parse_unified_diff(unified_diff)

    assert files == [
        FileDiff(
            path="README.md",
            patch=unified_diff,
            added_lines=((1, "new"),),
        )
    ]


def test_parse_unified_diff_returns_multiple_files() -> None:
    unified_diff = (
        "--- /dev/null\n"
        "+++ b/first.py\n"
        "@@ -0,0 +1 @@\n"
        "+first\n"
        "--- a/second.py\n"
        "+++ b/second.py\n"
        "@@ -1 +1 @@\n"
        "-before\n"
        "+after\n"
    )

    files = parse_unified_diff(unified_diff)

    assert [file_diff.path for file_diff in files] == ["first.py", "second.py"]
    assert files[0].added_lines == ((1, "first"),)
    assert files[1].added_lines == ((1, "after"),)


def test_parse_unified_diff_rejects_malformed_hunk_with_typed_error() -> None:
    unified_diff = (
        "diff --git a/file.py b/file.py\n"
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1,2 +1 @@\n"
        "-before\n"
        "+after\n"
    )

    with pytest.raises(DiffParseError, match="line counts"):
        parse_unified_diff(unified_diff)


def test_parse_unified_diff_rejects_content_after_completed_hunk() -> None:
    unified_diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1 +1 @@\n"
        "-before\n"
        "+after\n"
        "unexpected trailing content\n"
    )

    with pytest.raises(DiffParseError):
        parse_unified_diff(unified_diff)


def test_parse_unified_diff_accepts_no_newline_metadata_after_hunk_lines() -> None:
    unified_diff = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1 +1 @@\n"
        "-before\n"
        "\\ No newline at end of file\n"
        "+after\n"
        "\\ No newline at end of file\n"
    )

    files = parse_unified_diff(unified_diff)

    assert files[0].added_lines == ((1, "after"),)
