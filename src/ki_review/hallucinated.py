import ast
import re
import sys
from importlib.util import find_spec

from ki_review.models import FileDiff, Finding, build_finding

_VERSION_GUARD = re.compile(
    r"^(?P<indent>\s*)if\s+sys\.version_info(?:\[:2\])?\s*"
    r"(?P<operator>>=|<=|==|!=|>|<)\s*\(\s*(?P<major>\d+)\s*,\s*"
    r"(?P<minor>\d+)\s*\)\s*:"
)
_REMOVED_PANDAS_API = re.compile(
    r"\b(?:(?:df|dataframe|data_frame|series|frame)\."
    r"|(?:pd|pandas)\.(?:DataFrame|Series)\.)"
    r"(?P<method>append|iteritems|lookup)\s*\("
)
_REMOVED_PANDAS_MESSAGES = {
    "append": (
        "pandas DataFrame/Series.append was removed in pandas 2.0; use pandas.concat()."
    ),
    "iteritems": (
        "pandas DataFrame/Series.iteritems was removed in pandas 2.0; use .items()."
    ),
    "lookup": "pandas DataFrame.lookup was removed in pandas 2.0.",
}


def check_hallucinated_apis(files: list[FileDiff]) -> list[Finding]:
    findings: list[Finding] = []
    for file_diff in files:
        version_guards: list[tuple[int, bool]] = []
        for line_number, source_line in file_diff.added_lines:
            stripped_line = source_line.strip()
            if not stripped_line:
                continue
            indentation = len(source_line) - len(source_line.lstrip())

            if stripped_line == "else:" and version_guards:
                guard_indentation, guard_is_active = version_guards[-1]
                if indentation == guard_indentation:
                    version_guards[-1] = (guard_indentation, not guard_is_active)
                    continue

            while version_guards and indentation <= version_guards[-1][0]:
                version_guards.pop()

            version_guard = _VERSION_GUARD.match(source_line)
            if version_guard is not None:
                required_version = (
                    int(version_guard.group("major")),
                    int(version_guard.group("minor")),
                )
                version_guards.append(
                    (
                        indentation,
                        _version_condition_is_active(
                            version_guard.group("operator"), required_version
                        ),
                    )
                )
                continue

            if any(not guard_is_active for _, guard_is_active in version_guards):
                continue

            for module_name, imported_names in _imports(source_line):
                if not _module_is_available(module_name):
                    findings.append(
                        build_finding(
                            code="API001",
                            message=(
                                f"Imported module '{module_name}' is unavailable "
                                "in the current environment."
                            ),
                            severity="high",
                            path=file_diff.path,
                            line=line_number,
                        )
                    )
                    continue
                for imported_name in imported_names:
                    if imported_name == "*" or _imported_name_is_available(
                        module_name, imported_name
                    ):
                        continue
                    findings.append(
                        build_finding(
                            code="API001",
                            message=(
                                f"Imported name '{imported_name}' is unavailable "
                                f"from module '{module_name}'."
                            ),
                            severity="high",
                            path=file_diff.path,
                            line=line_number,
                        )
                    )
            removed_api = _REMOVED_PANDAS_API.search(source_line)
            if removed_api is not None:
                method = removed_api.group("method")
                findings.append(
                    build_finding(
                        code="API002",
                        message=_REMOVED_PANDAS_MESSAGES[method],
                        severity="high",
                        path=file_diff.path,
                        line=line_number,
                    )
                )

    return findings


def _imports(source_line: str) -> list[tuple[str, tuple[str, ...]]]:
    try:
        syntax_tree = ast.parse(source_line.lstrip())
    except SyntaxError:
        return []

    imports: list[tuple[str, tuple[str, ...]]] = []
    for statement in syntax_tree.body:
        if isinstance(statement, ast.Import):
            imports.extend((alias.name, ()) for alias in statement.names)
        elif isinstance(statement, ast.ImportFrom) and statement.level == 0:
            if statement.module is not None:
                imports.append(
                    (statement.module, tuple(alias.name for alias in statement.names))
                )
    return imports


def _imported_name_is_available(module_name: str, imported_name: str) -> bool:
    imported_module = __import__(module_name, fromlist=[imported_name])
    return hasattr(imported_module, imported_name)


def _module_is_available(module_name: str) -> bool:
    try:
        return find_spec(module_name) is not None
    except ModuleNotFoundError:
        return False


def _version_condition_is_active(
    operator: str, required_version: tuple[int, int]
) -> bool:
    current_version = sys.version_info[:2]
    if operator == ">=":
        return current_version >= required_version
    if operator == "<=":
        return current_version <= required_version
    if operator == "==":
        return current_version == required_version
    if operator == "!=":
        return current_version != required_version
    if operator == ">":
        return current_version > required_version
    return current_version < required_version
