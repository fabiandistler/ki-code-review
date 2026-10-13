from dataclasses import dataclass


@dataclass(frozen=True)
class FileDiff:
    path: str
    patch: str
    added_lines: tuple[tuple[int, str], ...] = ()
