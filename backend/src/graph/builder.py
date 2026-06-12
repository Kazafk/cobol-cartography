from pathlib import Path

from ..indexing.dependency_extractor import DependencyKind
from ..indexing.jcl_extractor import JclRefKind
from ..indexing.scanner import WorkspaceInventory
from .store import Edge, GraphStore, Node

_SQL_VERB_TO_RELATION = {
    "SELECT": "READS_TABLE",
    "INSERT": "WRITES_TABLE",
    "UPDATE": "UPDATES_TABLE",
    "DELETE": "DELETES_FROM_TABLE",
}


def _program_id(name: str) -> str:
    return f"program:{name.upper()}"


def _copybook_id(name: str) -> str:
    return f"copybook:{name.upper()}"


def _table_id(name: str) -> str:
    return f"db2table:{name.upper()}"


def _job_id(name: str) -> str:
    return f"jcl_job:{name.upper()}"


def _step_id(job: str, step: str) -> str:
    return f"jcl_step:{job.upper()}:{step.upper()}"


def build_graph(inventory: WorkspaceInventory, store: GraphStore) -> None:
    # --- program nodes ---
    for src in inventory.programs:
        name = Path(src.path).stem.upper()
        store.upsert_node(Node(
            id=_program_id(name), kind="program", name=name, path=src.path,
            properties={"size_bytes": src.size_bytes, "sha256": src.sha256},
        ))

    # --- copybook nodes ---
    for src in inventory.copybooks:
        name = Path(src.path).stem.upper()
        store.upsert_node(Node(
            id=_copybook_id(name), kind="copybook", name=name, path=src.path,
            properties={"size_bytes": src.size_bytes, "sha256": src.sha256},
        ))

    # --- INCLUDES_COPYBOOK edges ---
    for ref in inventory.copybook_refs:
        if not ref.is_resolved:
            continue
        pgm = Path(ref.source_file).stem.upper()
        cpy = Path(ref.resolved_path).stem.upper()
        store.upsert_edge(Edge(
            from_id=_program_id(pgm), to_id=_copybook_id(cpy),
            relation="INCLUDES_COPYBOOK", confidence=1.0,
            properties={"line": ref.line},
        ))

    # --- COBOL dependency edges ---
    for dep in inventory.dependency_refs:
        pgm = Path(dep.source_file).stem.upper()

        if dep.kind == DependencyKind.CALL and dep.target_is_literal:
            store.upsert_node(Node(id=_program_id(dep.target), kind="program", name=dep.target))
            store.upsert_edge(Edge(
                from_id=_program_id(pgm), to_id=_program_id(dep.target),
                relation="CALLS_PROGRAM", confidence=1.0,
                properties={"line": dep.line},
            ))

        elif dep.kind == DependencyKind.EXEC_CICS:
            if dep.target == "LINK" and dep.detail:
                store.upsert_node(Node(id=_program_id(dep.detail), kind="program", name=dep.detail))
                store.upsert_edge(Edge(
                    from_id=_program_id(pgm), to_id=_program_id(dep.detail),
                    relation="CICS_LINKS_PROGRAM", confidence=1.0,
                    properties={"line": dep.line},
                ))
            elif dep.target == "XCTL" and dep.detail:
                store.upsert_node(Node(id=_program_id(dep.detail), kind="program", name=dep.detail))
                store.upsert_edge(Edge(
                    from_id=_program_id(pgm), to_id=_program_id(dep.detail),
                    relation="CICS_XCTLS_PROGRAM", confidence=1.0,
                    properties={"line": dep.line},
                ))

        elif dep.kind == DependencyKind.EXEC_SQL and dep.detail:
            if dep.target == "INCLUDE":
                continue  # copybook reference — handled via copybook_refs, not as a table
            relation = _SQL_VERB_TO_RELATION.get(dep.target, "ACCESSES_TABLE")
            store.upsert_node(Node(id=_table_id(dep.detail), kind="db2table", name=dep.detail))
            store.upsert_edge(Edge(
                from_id=_program_id(pgm), to_id=_table_id(dep.detail),
                relation=relation, confidence=1.0,
                properties={"line": dep.line},
            ))

    # --- JCL nodes and edges ---
    current_job: str | None = None
    for ref in inventory.jcl_refs:
        src_stem = Path(ref.source_file).stem.upper()

        if ref.kind == JclRefKind.JOB:
            current_job = ref.name
            store.upsert_node(Node(
                id=_job_id(ref.name), kind="jcl_job", name=ref.name,
                path=ref.source_file,
            ))

        elif ref.kind == JclRefKind.EXEC_PGM and ref.target:
            job_name = current_job or src_stem
            sid = _step_id(job_name, ref.name)
            store.upsert_node(Node(
                id=sid, kind="jcl_step", name=ref.name,
                properties={"program": ref.target, "job": job_name},
            ))
            store.upsert_edge(Edge(
                from_id=_job_id(job_name), to_id=sid,
                relation="HAS_STEP", confidence=1.0,
                properties={"line": ref.line},
            ))
            store.upsert_node(Node(id=_program_id(ref.target), kind="program", name=ref.target))
            store.upsert_edge(Edge(
                from_id=sid, to_id=_program_id(ref.target),
                relation="EXECUTES_PROGRAM", confidence=1.0,
                properties={"line": ref.line},
            ))

        elif ref.kind == JclRefKind.EXEC_PROC and ref.target:
            job_name = current_job or src_stem
            sid = _step_id(job_name, ref.name)
            store.upsert_node(Node(
                id=sid, kind="jcl_step", name=ref.name,
                properties={"proc": ref.target, "job": job_name},
            ))
            store.upsert_edge(Edge(
                from_id=_job_id(job_name), to_id=sid,
                relation="HAS_STEP", confidence=1.0,
                properties={"line": ref.line},
            ))
