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
