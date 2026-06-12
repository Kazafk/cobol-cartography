import re
from dataclasses import dataclass
from enum import Enum


class JclRefKind(str, Enum):
    JOB = "job"
    EXEC_PGM = "exec_pgm"
    EXEC_PROC = "exec_proc"
    DD = "dd"


@dataclass
class JclRef:
    kind: JclRefKind
    source_file: str
    line: int
    name: str          # job name, step name, or DD name
    target: str | None  # PGM name, PROC name, or DSN


# JCL statement: //name keyword params  (name = cols 3-10)
_STMT_RE = re.compile(
    r"^//([A-Z0-9@#$]{1,8})\s+(JOB|EXEC|DD)\b(.*)",
    re.IGNORECASE,
)
_COMMENT_RE = re.compile(r"^//\*")
_CONTINUATION_RE = re.compile(r"^//\s")  # blank name = continuation

_PGM_RE = re.compile(r"\bPGM=([A-Z0-9@#$-]+)", re.IGNORECASE)
_PROC_RE = re.compile(r"\bPROC=([A-Z0-9@#$-]+)", re.IGNORECASE)
_DSN_RE = re.compile(r"\bDSN=([A-Z0-9@#$.()&-]+)", re.IGNORECASE)


def _parse_exec(params: str) -> tuple[JclRefKind, str | None]:
    pgm = _PGM_RE.search(params)
    if pgm:
        return JclRefKind.EXEC_PGM, pgm.group(1).upper()
    proc = _PROC_RE.search(params)
    if proc:
        return JclRefKind.EXEC_PROC, proc.group(1).upper()
    # implicit PROC: first token before comma or end
    first = params.strip().split()[0].split(",")[0] if params.strip() else None
    if first and not first.startswith("="):
        return JclRefKind.EXEC_PROC, first.upper()
    return JclRefKind.EXEC_PROC, None


def extract_jcl_dependencies(source_path: str) -> list[JclRef]:
    try:
        with open(source_path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return []

    refs: list[JclRef] = []
    for lineno, line in enumerate(lines, 1):
        if _COMMENT_RE.match(line) or _CONTINUATION_RE.match(line):
            continue
        m = _STMT_RE.match(line)
        if not m:
            continue
        name, keyword, params = m.group(1).upper(), m.group(2).upper(), m.group(3)

        if keyword == "JOB":
            refs.append(JclRef(kind=JclRefKind.JOB, source_file=source_path,
                                line=lineno, name=name, target=None))
        elif keyword == "EXEC":
            kind, target = _parse_exec(params)
            refs.append(JclRef(kind=kind, source_file=source_path,
                                line=lineno, name=name, target=target))
        elif keyword == "DD":
            dsn = _DSN_RE.search(params)
            refs.append(JclRef(kind=JclRefKind.DD, source_file=source_path,
                                line=lineno, name=name,
                                target=dsn.group(1).upper() if dsn else None))
    return refs
