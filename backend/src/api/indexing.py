import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator

from ..graph.builder import build_graph
from ..graph.store import GraphStore
from ..indexing.copybook_resolver import resolve_copybooks
from ..indexing.dependency_extractor import DependencyRef, extract_dependencies
from ..indexing.jcl_extractor import JclRef, extract_jcl_dependencies
from ..indexing.scanner import WorkspaceInventory, scan_workspace

router = APIRouter(prefix="/api", tags=["indexing"])

_inventories: dict[str, WorkspaceInventory] = {}
_graph_store: GraphStore | None = None


def set_graph_store(store: GraphStore) -> None:
    global _graph_store
    _graph_store = store


class IndexRequest(BaseModel):
    workspacePath: str
    copybookPaths: list[str] = []
    sourceFormat: str = "fixed"
    incremental: bool = True

    @field_validator("workspacePath")
    @classmethod
    def validate_workspace_path(cls, v: str) -> str:
        p = Path(v).resolve()
        if not p.is_dir():
            raise ValueError(f"workspacePath is not an existing directory: {v}")
        return str(p)


class IndexResponse(BaseModel):
    jobId: str
    status: str
    programs: int
    copybooks: int
    jclJobs: int
    errors: int
    unresolvedCopybooks: int
    graphNodes: int
    graphEdges: int


class SourceFileOut(BaseModel):
    path: str
    relative_path: str
    kind: str
    size_bytes: int
    sha256: str


class CopybookRefOut(BaseModel):
    member_name: str
    source_file: str
    line: int
    resolved_path: Optional[str]
    is_resolved: bool


class DependencyRefOut(BaseModel):
    kind: str
    source_file: str
    line: int
    target: str
    target_is_literal: bool
    detail: Optional[str]


def _require_latest() -> WorkspaceInventory:
    inv = _inventories.get("latest")
    if inv is None:
        raise HTTPException(
            status_code=404,
            detail="No workspace indexed yet. Call POST /api/index/workspace first.",
        )
    return inv


def _to_out(f) -> SourceFileOut:
    return SourceFileOut(
        path=f.path,
        relative_path=f.relative_path,
        kind=f.kind.value,
        size_bytes=f.size_bytes,
        sha256=f.sha256,
    )


@router.post("/index/workspace", response_model=IndexResponse)
async def index_workspace(req: IndexRequest) -> IndexResponse:
    inventory = scan_workspace(req.workspacePath)

    inventory.copybook_refs = resolve_copybooks(
        programs=inventory.programs,
        known_copybooks=inventory.copybooks,
        extra_search_paths=req.copybookPaths,
    )

    all_deps: list[DependencyRef] = []
    for program in inventory.programs:
        all_deps.extend(extract_dependencies(program.path))
    inventory.dependency_refs = all_deps

    all_jcl: list[JclRef] = []
    for jcl_file in inventory.jcl_jobs:
        all_jcl.extend(extract_jcl_dependencies(jcl_file.path))
    inventory.jcl_refs = all_jcl

    store = _graph_store
    if store is not None:
        store.clear()
        build_graph(inventory, store)

    job_id = f"idx-{uuid.uuid4().hex[:8]}"
    _inventories[job_id] = inventory
    _inventories["latest"] = inventory

    unresolved = sum(1 for r in inventory.copybook_refs if not r.is_resolved)
    return IndexResponse(
        jobId=job_id,
        status="completed",
        programs=len(inventory.programs),
        copybooks=len(inventory.copybooks),
        jclJobs=len(inventory.jcl_jobs),
        errors=len(inventory.errors),
        unresolvedCopybooks=unresolved,
        graphNodes=store.node_count() if store else 0,
        graphEdges=store.edge_count() if store else 0,
    )


@router.get("/inventory/programs", response_model=list[SourceFileOut])
async def list_programs() -> list[SourceFileOut]:
    return [_to_out(f) for f in _require_latest().programs]


@router.get("/inventory/copybooks", response_model=list[SourceFileOut])
async def list_copybooks() -> list[SourceFileOut]:
    return [_to_out(f) for f in _require_latest().copybooks]


@router.get("/inventory/jobs", response_model=list[SourceFileOut])
async def list_jcl_jobs() -> list[SourceFileOut]:
    return [_to_out(f) for f in _require_latest().jcl_jobs]


@router.get("/inventory/dependencies", response_model=list[DependencyRefOut])
async def list_dependencies(
    kind: Optional[str] = Query(default=None),
) -> list[DependencyRefOut]:
    refs = _require_latest().dependency_refs
    if kind is not None:
        refs = [r for r in refs if r.kind.value == kind]
    return [
        DependencyRefOut(
            kind=r.kind.value,
            source_file=r.source_file,
            line=r.line,
            target=r.target,
            target_is_literal=r.target_is_literal,
            detail=r.detail,
        )
        for r in refs
    ]


@router.get("/inventory/copybook-refs", response_model=list[CopybookRefOut])
async def list_copybook_refs(
    resolved: Optional[bool] = Query(default=None),
) -> list[CopybookRefOut]:
    refs = _require_latest().copybook_refs
    if resolved is not None:
        refs = [r for r in refs if r.is_resolved == resolved]
    return [
        CopybookRefOut(
            member_name=r.member_name,
            source_file=r.source_file,
            line=r.line,
            resolved_path=r.resolved_path,
            is_resolved=r.is_resolved,
        )
        for r in refs
    ]
