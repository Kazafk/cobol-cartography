from collections import deque
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..graph.store import GraphStore

router = APIRouter(prefix="/api/impact", tags=["impact"])

_graph_store: GraphStore | None = None

_CALL_RELATIONS = ("CALLS_PROGRAM", "CICS_LINKS_PROGRAM", "CICS_XCTLS_PROGRAM")


def set_graph_store(store: GraphStore) -> None:
    global _graph_store
    _graph_store = store


def _require_store() -> GraphStore:
    if _graph_store is None:
        raise HTTPException(status_code=503, detail="Graph store not initialised.")
    return _graph_store


class ImpactEntry(BaseModel):
    name: str
    depth: int
    via: Optional[str] = None
    confidence: float = 1.0


class ImpactedJob(BaseModel):
    name: str


class CopybookImpact(BaseModel):
    copybook_name: str
    direct_impacts: list[ImpactEntry]
    indirect_impacts: list[ImpactEntry]
    uncertain_impacts: list[ImpactEntry]
    impacted_jobs: list[ImpactedJob]
    total_programs: int
    total_jobs: int


class TableImpactEntry(BaseModel):
    name: str
    confidence: float = 1.0


class TableImpact(BaseModel):
    table_name: str
    readers: list[TableImpactEntry]
    writers: list[TableImpactEntry]
    updaters: list[TableImpactEntry]
    deleters: list[TableImpactEntry]
    associated_jobs: list[ImpactedJob]


_TABLE_RELATIONS = {
    "READS_TABLE": "readers",
    "WRITES_TABLE": "writers",
    "UPDATES_TABLE": "updaters",
    "DELETES_FROM_TABLE": "deleters",
}


@router.get("/table/{name}", response_model=TableImpact)
async def get_table_impact(name: str) -> TableImpact:
    store = _require_store()
    table_id = f"db2table:{name.upper()}"
    if store.get_node(table_id) is None:
        raise HTTPException(status_code=404, detail=f"Table '{name.upper()}' not found in graph.")

    readers: list[TableImpactEntry] = []
    writers: list[TableImpactEntry] = []
    updaters: list[TableImpactEntry] = []
    deleters: list[TableImpactEntry] = []
    seen_programs: set[str] = set()

    buckets = {"readers": readers, "writers": writers, "updaters": updaters, "deleters": deleters}

    for rel, bucket_key in _TABLE_RELATIONS.items():
        for edge in store.get_incoming(table_id, rel):
            pgm_id = edge.from_id
            if pgm_id.startswith("program:"):
                pgm_name = pgm_id.split(":", 1)[1]
                buckets[bucket_key].append(TableImpactEntry(name=pgm_name, confidence=edge.confidence))
                seen_programs.add(pgm_id)

    seen_jobs: set[str] = set()
    associated_jobs: list[ImpactedJob] = []
    for pgm_id in seen_programs:
        for edge in store.get_incoming(pgm_id, "EXECUTES_PROGRAM"):
            parts = edge.from_id.split(":")  # jcl_step:JOBNAME:STEPNAME
            if len(parts) >= 3:
                job_name = parts[1]
                if job_name not in seen_jobs:
                    seen_jobs.add(job_name)
                    associated_jobs.append(ImpactedJob(name=job_name))

    return TableImpact(
        table_name=name.upper(),
        readers=readers,
        writers=writers,
        updaters=updaters,
        deleters=deleters,
        associated_jobs=associated_jobs,
    )


@router.get("/copybook/{name}", response_model=CopybookImpact)
async def get_copybook_impact(name: str) -> CopybookImpact:
    store = _require_store()
    copybook_id = f"copybook:{name.upper()}"
    if store.get_node(copybook_id) is None:
        raise HTTPException(status_code=404, detail=f"Copybook '{name.upper()}' not found in graph.")

    visited: set[str] = set()

    # Depth-1: programs that directly include this copybook
    direct: list[ImpactEntry] = []
    for edge in store.get_incoming(copybook_id, "INCLUDES_COPYBOOK"):
        pgm_id = edge.from_id
        if pgm_id.startswith("program:") and pgm_id not in visited:
            visited.add(pgm_id)
            direct.append(ImpactEntry(name=pgm_id.split(":", 1)[1], depth=1))

    # BFS backward through the call graph to find indirect impacts
    indirect: list[ImpactEntry] = []
    queue: deque[tuple[str, int, str]] = deque(
        (f"program:{e.name}", 1, e.name) for e in direct
    )

    while queue:
        current_id, current_depth, current_name = queue.popleft()
        for rel in _CALL_RELATIONS:
            for edge in store.get_incoming(current_id, rel):
                caller_id = edge.from_id
                if caller_id.startswith("program:") and caller_id not in visited:
                    visited.add(caller_id)
                    caller_name = caller_id.split(":", 1)[1]
                    indirect.append(ImpactEntry(
                        name=caller_name,
                        depth=current_depth + 1,
                        via=current_name,
                    ))
                    queue.append((caller_id, current_depth + 1, caller_name))

    # Find JCL jobs that execute any impacted program
    seen_jobs: set[str] = set()
    impacted_jobs: list[ImpactedJob] = []
    for pgm_id in visited:
        for edge in store.get_incoming(pgm_id, "EXECUTES_PROGRAM"):
            parts = edge.from_id.split(":")  # jcl_step:JOBNAME:STEPNAME
            if len(parts) >= 3:
                job_name = parts[1]
                if job_name not in seen_jobs:
                    seen_jobs.add(job_name)
                    impacted_jobs.append(ImpactedJob(name=job_name))

    total_programs = len(direct) + len(indirect)
    return CopybookImpact(
        copybook_name=name.upper(),
        direct_impacts=direct,
        indirect_impacts=indirect,
        uncertain_impacts=[],
        impacted_jobs=impacted_jobs,
        total_programs=total_programs,
        total_jobs=len(impacted_jobs),
    )
