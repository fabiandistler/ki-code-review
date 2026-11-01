import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"

FULL_GATE = (
    "uv run pytest",
    "uv run ruff check .",
    "uv run ruff format --check .",
    "uv run pyright",
)


def test_ci_workflow_runs_on_pull_request_and_push_to_main() -> None:
    workflow = WORKFLOW.read_text()
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "branches: [main]" in workflow


def test_ci_workflow_ignores_plan_changes() -> None:
    workflow = WORKFLOW.read_text()
    assert workflow.count('paths-ignore: ["plans/**"]') == 2


def test_ci_workflow_runs_full_gate() -> None:
    workflow = WORKFLOW.read_text()
    for command in FULL_GATE:
        assert f"run: {command}" in workflow


def test_ci_workflow_pins_setup_uv_to_a_commit_sha() -> None:
    # astral-sh/setup-uv publishes no floating major tags since v8, so a ref
    # like `@v10` does not resolve and the job fails before any step runs.
    workflow = WORKFLOW.read_text()
    pinned_ref = r"uses: astral-sh/setup-uv@[0-9a-f]{40} # v\d+\.\d+\.\d+$"
    assert re.search(pinned_ref, workflow, re.MULTILINE) is not None
