import re
from dataclasses import dataclass
from enum import Enum


class DependencyKind(str, Enum):
    CALL = "call"
    PERFORM = "perform"
    EXEC_CICS = "exec_cics"
    EXEC_SQL = "exec_sql"


@dataclass
class DependencyRef:
    kind: DependencyKind
    source_file: str
    line: int
    target: str
    target_is_literal: bool = True
    detail: str | None = None


# --- compiled patterns ---

_CALL_LITERAL_RE = re.compile(r"\bCALL\s+['\"]([A-Za-z0-9#@$-]+)['\"]", re.IGNORECASE)
_CALL_DYNAMIC_RE = re.compile(r"\bCALL\s+([A-Za-z0-9#@$-]+)", re.IGNORECASE)

_PERFORM_RE = re.compile(r"\bPERFORM\s+([A-Za-z0-9#@$-]+)", re.IGNORECASE)
_PERFORM_NON_TARGETS = {
    "VARYING", "UNTIL", "WITH", "TEST", "AFTER", "BEFORE", "INLINE",
}

_EXEC_CICS_START = re.compile(r"\bEXEC\s+CICS\b", re.IGNORECASE)
_EXEC_SQL_START = re.compile(r"\bEXEC\s+SQL\b", re.IGNORECASE)
_END_EXEC = re.compile(r"\bEND-EXEC\b", re.IGNORECASE)

_CICS_VERB_RE = re.compile(r"\bEXEC\s+CICS\s+(\w+)", re.IGNORECASE | re.DOTALL)
_CICS_PROGRAM_RE = re.compile(
    r"\bPROGRAM\s*\(\s*['\"]?([A-Za-z0-9#@$-]+)['\"]?\s*\)", re.IGNORECASE
)

_SQL_VERB_RE = re.compile(r"\bEXEC\s+SQL\s+(\w+)", re.IGNORECASE | re.DOTALL)
_SQL_FROM_RE = re.compile(r"\bFROM\s+([A-Za-z][A-Za-z0-9_#@$]*)", re.IGNORECASE)
_SQL_INSERT_INTO_RE = re.compile(
    r"\bINSERT\s+INTO\s+([A-Za-z][A-Za-z0-9_#@$]*)", re.IGNORECASE
)
_SQL_UPDATE_RE = re.compile(r"\bUPDATE\s+([A-Za-z][A-Za-z0-9_#@$]*)", re.IGNORECASE)
_SQL_JOIN_RE = re.compile(r"\bJOIN\s+([A-Za-z][A-Za-z0-9_#@$]*)", re.IGNORECASE)
_SQL_INCLUDE_RE = re.compile(r"\bINCLUDE\s+([A-Za-z0-9_#@$]+)", re.IGNORECASE)

_SQL_NON_TABLE = {
    "SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "AND", "OR",
    "NOT", "IN", "VALUES", "SET", "INTO", "HAVING", "GROUP", "ORDER", "BY",
    "COMMIT", "ROLLBACK", "DECLARE", "CURSOR", "FOR", "OPEN", "CLOSE",
    "FETCH", "WHENEVER", "DISTINCT", "ALL", "AS", "ON", "INNER", "OUTER",
    "LEFT", "RIGHT", "FULL", "CROSS", "NATURAL", "UNION", "EXCEPT",
    "INTERSECT", "SQLCA", "SQLCODE", "SQLSTATE",
}


def _is_comment(line: str) -> bool:
    return len(line) >= 7 and line[6] == "*"


def _collect_block(lines: list[str], start: int) -> tuple[str, int]:
    """Collect lines from start until END-EXEC (inclusive). Returns (block_text, end_index)."""
    block: list[str] = []
    i = start
    while i < len(lines):
        block.append(lines[i])
        if _END_EXEC.search(lines[i]):
            break
        i += 1
    return " ".join(block), i


def _extract_cics(source_file: str, start_line: int, block: str) -> list[DependencyRef]:
    refs: list[DependencyRef] = []
    m = _CICS_VERB_RE.search(block)
    if not m:
        return refs
    verb = m.group(1).upper()
    detail: str | None = None
    pm = _CICS_PROGRAM_RE.search(block)
    if pm:
        detail = pm.group(1).upper()
    refs.append(
        DependencyRef(
            kind=DependencyKind.EXEC_CICS,
            source_file=source_file,
            line=start_line,
            target=verb,
            detail=detail,
        )
    )
    return refs


def _extract_sql(source_file: str, start_line: int, block: str) -> list[DependencyRef]:
    refs: list[DependencyRef] = []
    vm = _SQL_VERB_RE.search(block)
    if not vm:
        return refs
    verb = vm.group(1).upper()

    if verb == "INCLUDE":
        im = _SQL_INCLUDE_RE.search(block)
        if im:
            refs.append(
                DependencyRef(
                    kind=DependencyKind.EXEC_SQL,
                    source_file=source_file,
                    line=start_line,
                    target=verb,
                    detail=im.group(1).upper(),
                )
            )
        return refs

    # Collect table names from the block
    table_names: list[str] = []
    for pattern in (_SQL_FROM_RE, _SQL_INSERT_INTO_RE, _SQL_UPDATE_RE, _SQL_JOIN_RE):
        for m in pattern.finditer(block):
            name = m.group(1).upper()
            if name not in _SQL_NON_TABLE:
                table_names.append(name)

    if table_names:
        for table in dict.fromkeys(table_names):  # deduplicated, order-preserving
            refs.append(
                DependencyRef(
                    kind=DependencyKind.EXEC_SQL,
                    source_file=source_file,
                    line=start_line,
                    target=verb,
                    detail=table,
                )
            )
    else:
        refs.append(
            DependencyRef(
                kind=DependencyKind.EXEC_SQL,
                source_file=source_file,
                line=start_line,
                target=verb,
            )
        )
    return refs


def extract_dependencies(source_path: str) -> list[DependencyRef]:
    try:
        with open(source_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []

    refs: list[DependencyRef] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        lineno = i + 1

        if _is_comment(line):
            i += 1
            continue

        upper = line.upper()

        if _EXEC_SQL_START.search(upper):
            block, i = _collect_block(lines, i)
            refs.extend(_extract_sql(source_path, lineno, block))
            i += 1
            continue

        if _EXEC_CICS_START.search(upper):
            block, i = _collect_block(lines, i)
            refs.extend(_extract_cics(source_path, lineno, block))
            i += 1
            continue

        m = _CALL_LITERAL_RE.search(line)
        if m:
            refs.append(
                DependencyRef(
                    kind=DependencyKind.CALL,
                    source_file=source_path,
                    line=lineno,
                    target=m.group(1).upper(),
                    target_is_literal=True,
                )
            )
            i += 1
            continue

        m = _CALL_DYNAMIC_RE.search(line)
        if m and m.group(1).upper() not in _PERFORM_NON_TARGETS:
            refs.append(
                DependencyRef(
                    kind=DependencyKind.CALL,
                    source_file=source_path,
                    line=lineno,
                    target=m.group(1).upper(),
                    target_is_literal=False,
                )
            )
            i += 1
            continue

        m = _PERFORM_RE.search(line)
        if m:
            target = m.group(1).upper()
            if target not in _PERFORM_NON_TARGETS:
                refs.append(
                    DependencyRef(
                        kind=DependencyKind.PERFORM,
                        source_file=source_path,
                        line=lineno,
                        target=target,
                    )
                )

        i += 1

    return refs
