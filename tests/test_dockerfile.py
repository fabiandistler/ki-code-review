import re
from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parent.parent / "Dockerfile"


def stages(dockerfile: str) -> dict[str, str]:
    """Map each named build stage to its body."""
    parts = re.split(r"^FROM .+ AS (\w+)$", dockerfile, flags=re.MULTILINE)
    return dict(zip(parts[1::2], parts[2::2], strict=True))


def test_dockerfile_has_base_test_and_runtime_stages() -> None:
    assert list(stages(DOCKERFILE.read_text())) == ["base", "test", "runtime"]


def test_dockerfile_pins_base_image_versions() -> None:
    for image in re.findall(r"^FROM (\S+)", DOCKERFILE.read_text(), re.MULTILINE):
        assert image in {"base", "test"} or re.search(r":\d", image), image
    assert re.search(r"ghcr\.io/astral-sh/uv:\d", DOCKERFILE.read_text())


def test_dockerfile_installs_only_from_lockfile() -> None:
    dockerfile = DOCKERFILE.read_text()
    syncs = re.findall(r"uv sync[^\n]*", dockerfile)
    assert syncs
    assert all("--locked" in sync for sync in syncs)


def test_test_stage_runs_suite() -> None:
    assert "RUN uv run pytest -q" in stages(DOCKERFILE.read_text())["test"]


def test_runtime_stage_exposes_port_8000_without_dev_dependencies() -> None:
    runtime = stages(DOCKERFILE.read_text())["runtime"]
    assert "EXPOSE 8000" in runtime
    assert "--no-dev" in runtime
