from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..graph.store import GraphStore, Node

router = APIRouter(prefix="/api/programs", tags=["programs"])

_graph_store: GraphStore | None = None

_CALL_RELATIONS = {"CALLS_PROGRAM", "CICS_LINKS_PROGRAM", "CICS_XCTLS_PROGRAM"}
_TABLE_RELATION_TO_ACCESS = {
    "READS_TABLE": "READ",
    "WRITES_TABLE": "WRITE",
    "UPDATES_TABLE": "UPDATE",
    "DELETES_FROM_TABLE": "DELETE",
}


def set_graph_store(store: GraphStore) -> None:
    global _graph_store
    _graph_store = store


def _require_store() -> GraphStore:
    if _graph_store is None:
        raise HTTPException(status_code=503, detail="Graph store not initialised.")
    return _graph_store


class NodeOut(BaseModel):
    id: str
    kind: str
    name: str
    path: Optional[str]
    properties: dict


class DependencyEdgeOut(BaseModel):
    relation: str
    confidence: float
    node: NodeOut
    line: Optional[int]


class ProgramDepsOut(BaseModel):
    program: NodeOut
    outgoing: list[DependencyEdgeOut]
    incoming: list[DependencyEdgeOut]


class ProgramCall(BaseModel):
    name: str
    relation: str
    line: Optional[int] = None


class TableAccess(BaseModel):
    name: str
    access: str


class JobExecution(BaseModel):
    job: str
    step: str


class SheetMetrics(BaseModel):
    copybooks_included: int
    programs_called: int
    tables_accessed: int
    called_by_count: int
    executed_by_jobs: int


class ProgramSheet(BaseModel):
    name: str
    path: Optional[str] = None
    size_bytes: Optional[int] = None
    metrics: SheetMetrics
    copybooks: list[str]
    calls: list[ProgramCall]
    called_by: list[ProgramCall]
    tables: list[TableAccess]
    executed_by: list[JobExecution]


def _node_out(n: Node) -> NodeOut:
    return NodeOut(id=n.id, kind=n.kind, name=n.name, path=n.path, properties=n.properties)


@router.get("/{name}/dependencies", response_model=ProgramDepsOut)
async def get_program_dependencies(name: str) -> ProgramDepsOut:
    store = _require_store()
    node_id = f"program:{name.upper()}"
    node = store.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Program '{name.upper()}' not found in graph.")

    outgoing: list[DependencyEdgeOut] = []
    for edge in store.get_outgoing(node_id):
        target = store.get_node(edge.to_id)
        if target:
            outgoing.append(DependencyEdgeOut(
                relation=edge.relation,
                confidence=edge.confidence,
                node=_node_out(target),
                line=edge.properties.get("line"),
            ))

    incoming: list[DependencyEdgeOut] = []
    for edge in store.get_incoming(node_id):
        source = store.get_node(edge.from_id)
        if source:
            incoming.append(DependencyEdgeOut(
                relation=edge.relation,
                confidence=edge.confidence,
                node=_node_out(source),
                line=edge.properties.get("line"),
            ))

    return ProgramDepsOut(
        program=_node_out(node),
        outgoing=outgoing,
        incoming=incoming,
    )


@router.get("/{name}/sheet", response_model=ProgramSheet)
async def get_program_sheet(name: str) -> ProgramSheet:
    store = _require_store()
    node_id = f"program:{name.upper()}"
    node = store.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Program '{name.upper()}' not found in graph.")

    outgoing = store.get_outgoing(node_id)
    incoming = store.get_incoming(node_id)

    copybooks = [
        e.to_id.split(":", 1)[1]
        for e in outgoing
        if e.relation == "INCLUDES_COPYBOOK"
    ]
    calls = [
        ProgramCall(name=e.to_id.split(":", 1)[1], relation=e.relation, line=e.properties.get("line"))
        for e in outgoing
        if e.relation in _CALL_RELATIONS
    ]
    tables = [
        TableAccess(name=e.to_id.split(":", 1)[1], access=_TABLE_RELATION_TO_ACCESS[e.relation])
        for e in outgoing
        if e.relation in _TABLE_RELATION_TO_ACCESS
    ]
    called_by = [
        ProgramCall(name=e.from_id.split(":", 1)[1], relation=e.relation, line=e.properties.get("line"))
        for e in incoming
        if e.relation in _CALL_RELATIONS
    ]
    executed_by: list[JobExecution] = []
    for e in incoming:
        if e.relation == "EXECUTES_PROGRAM":
            parts = e.from_id.split(":")  # jcl_step:JOBNAME:STEPNAME
            if len(parts) >= 3:
                executed_by.append(JobExecution(job=parts[1], step=parts[2]))

    return ProgramSheet(
        name=node.name,
        path=node.path,
        size_bytes=node.properties.get("size_bytes"),
        metrics=SheetMetrics(
            copybooks_included=len(copybooks),
            programs_called=len(calls),
            tables_accessed=len(tables),
            called_by_count=len(called_by),
            executed_by_jobs=len(executed_by),
        ),
        copybooks=copybooks,
        calls=calls,
        called_by=called_by,
        tables=tables,
        executed_by=executed_by,
    )


@router.get("", response_model=list[NodeOut])
async def list_programs() -> list[NodeOut]:
    store = _require_store()
    return [_node_out(n) for n in store.list_nodes("program")]
