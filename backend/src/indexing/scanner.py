import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FileKind(str, Enum):
    PROGRAM = "program"
    COPYBOOK = "copybook"
    JCL = "jcl"


_PROGRAM_EXTS = {".cbl", ".cob", ".cobol"}
_COPYBOOK_EXTS = {".cpy", ".copy"}
_JCL_EXTS = {".jcl"}


def _classify(suffix: str) -> FileKind | None:
    s = suffix.lower()
    if s in _PROGRAM_EXTS:
        return FileKind.PROGRAM
    if s in _COPYBOOK_EXTS:
        return FileKind.COPYBOOK
    if s in _JCL_EXTS:
        return FileKind.JCL
    return None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class SourceFile:
    path: str
    relative_path: str
    kind: FileKind
    size_bytes: int
    sha256: str


@dataclass
class ScanError:
    file: str
    stage: str
    error: str
    severity: str


@dataclass
class WorkspaceInventory:
    workspace_path: str
    programs: list[SourceFile] = field(default_factory=list)
    copybooks: list[SourceFile] = field(default_factory=list)
    jcl_jobs: list[SourceFile] = field(default_factory=list)
    errors: list[ScanError] = field(default_factory=list)
    copybook_refs: list = field(default_factory=list)   # list[CopybookRef]
    dependency_refs: list = field(default_factory=list)  # list[DependencyRef]
    jcl_refs: list = field(default_factory=list)         # list[JclRef]


def scan_workspace(workspace_path: str) -> WorkspaceInventory:
    root = Path(workspace_path).resolve()
    inventory = WorkspaceInventory(workspace_path=str(root))

    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        kind = _classify(file_path.suffix)
        if kind is None:
            continue
        try:
            source = SourceFile(
                path=str(file_path),
                relative_path=str(file_path.relative_to(root)),
                kind=kind,
                size_bytes=file_path.stat().st_size,
                sha256=_sha256(file_path),
            )
            if kind == FileKind.PROGRAM:
                inventory.programs.append(source)
            elif kind == FileKind.COPYBOOK:
                inventory.copybooks.append(source)
            elif kind == FileKind.JCL:
                inventory.jcl_jobs.append(source)
        except OSError as exc:
            inventory.errors.append(
                ScanError(
                    file=str(file_path),
                    stage="scan",
                    error=str(exc),
                    severity="warning",
                )
            )

    return inventory
