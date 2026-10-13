from ki_review.models import FileDiff


def test_file_diff_keeps_path_patch_and_added_line_numbers() -> None:
    file_diff = FileDiff(
        path="src/store.py",
        patch="@@ -1 +1 @@\n-old\n+new",
        added_lines=((1, "new"),),
    )

    assert file_diff.path == "src/store.py"
    assert file_diff.patch == "@@ -1 +1 @@\n-old\n+new"
    assert file_diff.added_lines == ((1, "new"),)
