import re

from ki_review.models import FileDiff

_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class DiffParseError(ValueError):
    """Raised when a unified diff cannot be parsed."""


def parse_unified_diff(text: str) -> list[FileDiff]:
    if not text.strip():
        raise DiffParseError("Unified diff is empty")

    lines = text.splitlines(keepends=True)
    git_file_starts = [
        line_index
        for line_index, line in enumerate(lines)
        if line.startswith("diff --git ")
    ]
    if git_file_starts:
        if any(line.strip() for line in lines[: git_file_starts[0]]):
            raise DiffParseError("Unexpected content before the first file header")
        section_ends = [*git_file_starts[1:], len(lines)]
        sections = [
            lines[section_start:section_end]
            for section_start, section_end in zip(
                git_file_starts, section_ends, strict=True
            )
        ]
    else:
        sections = _split_plain_file_sections(lines)

    return [_parse_file_section(section) for section in sections]


def _split_plain_file_sections(lines: list[str]) -> list[list[str]]:
    sections: list[list[str]] = []
    line_index = 0
    while line_index < len(lines):
        if not lines[line_index].startswith("--- "):
            if lines[line_index].strip():
                raise DiffParseError("Unified diff has no file headers")
            line_index += 1
            continue
        if line_index + 1 >= len(lines) or not lines[line_index + 1].startswith("+++ "):
            raise DiffParseError("File diff is missing its +++ header")

        section_start = line_index
        line_index += 2
        while line_index < len(lines):
            line = lines[line_index].rstrip("\r\n")
            if line.startswith("@@"):
                line_index, _ = _parse_hunk(lines, line_index)
                continue
            if line.startswith("--- ") and line_index + 1 < len(lines):
                if lines[line_index + 1].startswith("+++ "):
                    break
            line_index += 1
        sections.append(lines[section_start:line_index])

    if not sections:
        raise DiffParseError("Unified diff has no file headers")
    return sections


def _parse_file_section(lines: list[str]) -> FileDiff:
    old_path: str | None = None
    new_path: str | None = None
    for line in lines:
        if line.startswith("@@"):
            break
        if line.startswith("--- "):
            old_path = _diff_path(line[4:])
        elif line.startswith("+++ "):
            new_path = _diff_path(line[4:])
        if old_path is not None and new_path is not None:
            break

    if old_path is None or new_path is None:
        raise DiffParseError("File diff is missing --- and +++ headers")
    path = old_path if new_path == "/dev/null" else new_path

    added_lines: list[tuple[int, str]] = []
    line_index = 0
    while line_index < len(lines):
        if lines[line_index].startswith("@@"):
            line_index, hunk_added_lines = _parse_hunk(lines, line_index)
            added_lines.extend(hunk_added_lines)
        else:
            line_index += 1

    return FileDiff(
        path=path,
        patch="".join(lines),
        added_lines=tuple(added_lines),
    )


def _parse_hunk(
    lines: list[str], header_index: int
) -> tuple[int, list[tuple[int, str]]]:
    header = lines[header_index].rstrip("\r\n")
    match = _HUNK_HEADER.match(header)
    if match is None:
        raise DiffParseError(f"Malformed hunk header: {header}")

    old_remaining = int(match.group(2) or "1")
    new_remaining = int(match.group(4) or "1")
    new_line_number = int(match.group(3))
    added_lines: list[tuple[int, str]] = []
    line_index = header_index + 1

    while old_remaining or new_remaining:
        if line_index >= len(lines):
            raise DiffParseError("Hunk ended before its declared line counts")

        hunk_line = lines[line_index].rstrip("\r\n")
        if hunk_line.startswith("@@"):
            raise DiffParseError("Hunk ended before its declared line counts")
        if hunk_line.startswith("\\ No newline at end of file"):
            line_index += 1
            continue
        if not hunk_line:
            raise DiffParseError("Hunk contains an empty line without a prefix")

        marker, content = hunk_line[0], hunk_line[1:]
        if marker == " ":
            old_remaining -= 1
            new_remaining -= 1
            new_line_number += 1
        elif marker == "-":
            old_remaining -= 1
        elif marker == "+":
            added_lines.append((new_line_number, content))
            new_remaining -= 1
            new_line_number += 1
        else:
            raise DiffParseError(f"Malformed hunk line: {hunk_line}")

        if old_remaining < 0 or new_remaining < 0:
            raise DiffParseError("Hunk contains more lines than its header declares")
        line_index += 1

    while line_index < len(lines) and lines[line_index].startswith(
        "\\ No newline at end of file"
    ):
        line_index += 1
    return line_index, added_lines


def _diff_path(header_path: str) -> str:
    path = header_path.rstrip("\r\n").split("\t", maxsplit=1)[0]
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path
