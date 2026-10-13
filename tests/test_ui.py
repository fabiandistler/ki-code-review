from ki_review.models import FileDiff
from ki_review.ui import render_review_page


def test_review_page_has_pr_url_and_pasted_diff_forms() -> None:
    page = render_review_page()

    assert 'action="/reviews"' in page
    assert 'name="pr_url"' in page
    assert 'name="diff"' in page
    assert "GitHub pull request URL" in page
    assert "Paste a unified diff" in page


def test_review_page_displays_each_file_and_escapes_diff_content() -> None:
    page = render_review_page(
        files=[
            FileDiff(
                path='<img src="x">',
                patch=(
                    "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n"
                    "-old\n+<script>alert(1)</script>\n"
                ),
            )
        ]
    )

    assert "&lt;img src=&quot;x&quot;&gt;" in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page
    assert "@@ -1 +1 @@" in page


def test_review_page_preserves_form_values_and_shows_errors() -> None:
    page = render_review_page(
        error_message="Paste a PR URL or a unified diff.",
        pr_url="https://github.com/owner/repo/pull/42",
        diff_text="--- a/file.py\n+++ b/file.py",
    )

    assert "Paste a PR URL or a unified diff." in page
    assert 'value="https://github.com/owner/repo/pull/42"' in page
    assert "--- a/file.py" in page
