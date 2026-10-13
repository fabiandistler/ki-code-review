from html import escape

from ki_review.models import FileDiff


def render_review_page(
    files: list[FileDiff] | tuple[FileDiff, ...] = (),
    *,
    error_message: str | None = None,
    pr_url: str = "",
    diff_text: str = "",
) -> str:
    error_section = ""
    if error_message is not None:
        error_section = f'<p class="error" role="alert">{escape(error_message)}</p>'

    file_sections = "".join(
        f'<section class="file-diff"><h2>{escape(file_diff.path)}</h2>'
        f"<pre><code>{escape(file_diff.patch)}</code></pre></section>"
        for file_diff in files
    )
    diff_heading = f"<h2>Changed files ({len(files)})</h2>" if files else ""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PR Diff Viewer</title>
  <style>
    :root {{ color-scheme: light dark; font: 16px/1.5 system-ui, sans-serif; }}
    body {{ margin: 0 auto; max-width: 1100px; padding: 2rem 1rem; }}
    h1 {{ margin-top: 0; }}
    form {{ margin-block: 1rem 2rem; }}
    label {{ display: block; font-weight: 600; margin-bottom: .35rem; }}
    input, textarea, button {{ font: inherit; }}
    input, textarea {{
      box-sizing: border-box;
      max-width: 100%;
      padding: .6rem;
      width: 100%;
    }}
    textarea {{ min-height: 12rem; }}
    button {{ cursor: pointer; margin-top: .5rem; padding: .5rem .8rem; }}
    .error {{ border-left: 4px solid #c33; padding: .5rem .75rem; }}
    .file-diff {{ border: 1px solid #8886; margin-block: 1rem; }}
    .file-diff h2 {{
      border-bottom: 1px solid #8886;
      font: 600 1rem/1.4 ui-monospace, monospace;
      margin: 0;
      overflow-wrap: anywhere;
      padding: .6rem .8rem;
    }}
    pre {{ margin: 0; overflow-x: auto; padding: .8rem; }}
    code {{ font: 13px/1.5 ui-monospace, monospace; white-space: pre; }}
  </style>
</head>
<body>
  <main>
    <h1>PR Diff Viewer</h1>
    <p>Paste a GitHub pull request URL or a unified diff to inspect its
      changed files.
    </p>
    {error_section}
    <section aria-labelledby="pr-url-heading">
      <h2 id="pr-url-heading">View a GitHub pull request</h2>
      <form action="/reviews" method="post">
        <label for="pr_url">GitHub pull request URL</label>
        <input id="pr_url" name="pr_url" type="url" value="{escape(pr_url)}" required>
        <button type="submit">View pull request</button>
      </form>
    </section>
    <section aria-labelledby="diff-heading">
      <h2 id="diff-heading">View a pasted diff</h2>
      <form action="/reviews" method="post">
        <label for="diff">Paste a unified diff</label>
        <textarea id="diff" name="diff" required>{escape(diff_text)}</textarea>
        <button type="submit">View diff</button>
      </form>
    </section>
    {diff_heading}
    {file_sections}
  </main>
</body>
</html>
"""
