from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..graph.store import GraphStore

router = APIRouter(prefix="/api/graph", tags=["graph"])

_graph_store: GraphStore | None = None


def set_graph_store(store: GraphStore) -> None:
    global _graph_store
    _graph_store = store


def _require_store() -> GraphStore:
    if _graph_store is None:
        raise HTTPException(status_code=503, detail="Graph store not initialised.")
    return _graph_store


class D3Node(BaseModel):
    id: str
    kind: str
    name: str
    path: Optional[str] = None


class D3Link(BaseModel):
    source: str
    target: str
    relation: str
    confidence: float


class GraphExport(BaseModel):
    nodes: list[D3Node]
    links: list[D3Link]


@router.get("/export", response_model=GraphExport)
async def export_graph() -> GraphExport:
    store = _require_store()
    nodes = [
        D3Node(id=n.id, kind=n.kind, name=n.name, path=n.path)
        for n in store.all_nodes()
    ]
    links = [
        D3Link(
            source=e.from_id,
            target=e.to_id,
            relation=e.relation,
            confidence=e.confidence,
        )
        for e in store.all_edges()
    ]
    return GraphExport(nodes=nodes, links=links)
