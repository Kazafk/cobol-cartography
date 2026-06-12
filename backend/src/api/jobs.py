from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..graph.store import GraphStore

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

_graph_store: GraphStore | None = None


def set_graph_store(store: GraphStore) -> None:
    global _graph_store
    _graph_store = store


def _require_store() -> GraphStore:
    if _graph_store is None:
        raise HTTPException(status_code=503, detail="Graph store not initialised.")
    return _graph_store


class StepExecution(BaseModel):
    step_name: str
    program_name: str
    program_path: Optional[str] = None


class JobPrograms(BaseModel):
    job_name: str
    steps: list[StepExecution]
    total_programs: int


@router.get("/{name}/programs", response_model=JobPrograms)
async def get_job_programs(name: str) -> JobPrograms:
    store = _require_store()
    job_id = f"jcl_job:{name.upper()}"
    if store.get_node(job_id) is None:
        raise HTTPException(status_code=404, detail=f"JCL job '{name.upper()}' not found in graph.")

    steps: list[StepExecution] = []
    seen_programs: set[str] = set()

    for step_edge in store.get_outgoing(job_id, "HAS_STEP"):
        step_id = step_edge.to_id  # jcl_step:JOBNAME:STEPNAME
        parts = step_id.split(":")
        step_name = parts[2] if len(parts) >= 3 else step_id

        for prog_edge in store.get_outgoing(step_id, "EXECUTES_PROGRAM"):
            prog_id = prog_edge.to_id  # program:PROGNAME
            prog_node = store.get_node(prog_id)
            prog_name = prog_id.split(":", 1)[1]
            steps.append(StepExecution(
                step_name=step_name,
                program_name=prog_name,
                program_path=prog_node.path if prog_node else None,
            ))
            seen_programs.add(prog_name)

    return JobPrograms(
        job_name=name.upper(),
        steps=steps,
        total_programs=len(seen_programs),
    )
