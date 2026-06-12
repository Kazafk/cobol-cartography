import re
from dataclasses import dataclass
from pathlib import Path

from .scanner import SourceFile

_COPY_RE = re.compile(r"\bCOPY\s+([A-Za-z0-9#@$-]+)", re.IGNORECASE)
_EXEC_SQL_RE = re.compile(r"\bEXEC\s+SQL\b", re.IGNORECASE)
_SQL_INCLUDE_RE = re.compile(r"\bINCLUDE\s+([A-Za-z0-9#@$-]+)", re.IGNORECASE)
_END_EXEC_RE = re.compile(r"\bEND-EXEC\b", re.IGNORECASE)
_COPY_EXTS = {"", ".cpy", ".copy"}


@dataclass
class CopybookRef:
    member_name: str
    source_file: str
    line: int
    resolved_path: str | None
    is_resolved: bool


def extract_copy_statements(source_path: str) -> list[tuple[str, int]]:
    """Return (member_name_upper, line_number) for every COPY or EXEC SQL INCLUDE found."""
    refs: list[tuple[str, int]] = []
    try:
        with open(source_path, encoding="utf-8", errors="replace") as f:
            in_exec_sql = False
            for lineno, raw_line in enumerate(f, 1):
                # Skip fixed-format comment lines (asterisk in column 7)
                if len(raw_line) >= 7 and raw_line[6] == "*":
                    continue

                if in_exec_sql:
                    m = _SQL_INCLUDE_RE.search(raw_line)
                    if m:
                        refs.append((m.group(1).upper(), lineno))
                    if _END_EXEC_RE.search(raw_line):
                        in_exec_sql = False
                else:
                    if _EXEC_SQL_RE.search(raw_line):
                        m = _SQL_INCLUDE_RE.search(raw_line)
                        if m:
                            refs.append((m.group(1).upper(), lineno))
                        if not _END_EXEC_RE.search(raw_line):
                            in_exec_sql = True
                    else:
                        m = _COPY_RE.search(raw_line)
                        if m:
                            refs.append((m.group(1).upper(), lineno))
    except OSError:
        pass
    return refs


def _build_extra_index(extra_search_paths: list[str]) -> dict[str, str]:
    """Index stem→path for all copybook-like files in the extra search dirs."""
    index: dict[str, str] = {}
    for raw_path in extra_search_paths:
        p = Path(raw_path).resolve()
        if not p.is_dir():
            continue
        for f in p.iterdir():
            if f.is_file() and f.suffix.lower() in _COPY_EXTS:
                index[f.stem.upper()] = str(f)
    return index


def resolve_copybooks(
    programs: list[SourceFile],
    known_copybooks: list[SourceFile],
    extra_search_paths: list[str] | None = None,
) -> list[CopybookRef]:
    """
    For every COPY statement in every program, attempt to resolve the member
    name against (1) already-scanned copybooks and (2) extra search paths.
    """
    known_by_stem: dict[str, str] = {
        Path(c.path).stem.upper(): c.path for c in known_copybooks
    }
    extra_by_stem = _build_extra_index(extra_search_paths or [])

    refs: list[CopybookRef] = []
    for program in programs:
        for member_name, line in extract_copy_statements(program.path):
            resolved_path = known_by_stem.get(member_name) or extra_by_stem.get(member_name)
            refs.append(
                CopybookRef(
                    member_name=member_name,
                    source_file=program.path,
                    line=line,
                    resolved_path=resolved_path,
                    is_resolved=resolved_path is not None,
                )
            )
    return refs
