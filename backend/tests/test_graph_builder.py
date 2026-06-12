from pathlib import Path

import pytest

from src.graph.builder import build_graph
from src.graph.store import GraphStore
from src.indexing.copybook_resolver import CopybookRef
from src.indexing.dependency_extractor import DependencyKind, DependencyRef
from src.indexing.jcl_extractor import JclRef, JclRefKind
from src.indexing.scanner import FileKind, SourceFile, WorkspaceInventory


def _pgm(path: str) -> SourceFile:
    return SourceFile(path=path, relative_path=path, kind=FileKind.PROGRAM, size_bytes=0, sha256="aa")


def _cpy(path: str) -> SourceFile:
    return SourceFile(path=path, relative_path=path, kind=FileKind.COPYBOOK, size_bytes=0, sha256="bb")


def _jcl(path: str) -> SourceFile:
    return SourceFile(path=path, relative_path=path, kind=FileKind.JCL, size_bytes=0, sha256="cc")


@pytest.fixture
def store():
    return GraphStore()


def test_program_nodes_created(store):
    inv = WorkspaceInventory(workspace_path="/ws",
                             programs=[_pgm("/ws/PGMA.cbl"), _pgm("/ws/PGMB.cbl")])
    build_graph(inv, store)
    assert store.node_count("program") == 2
    assert store.get_node("program:PGMA") is not None


def test_copybook_nodes_created(store):
    inv = WorkspaceInventory(workspace_path="/ws",
                             copybooks=[_cpy("/ws/CPYA.cpy")])
    build_graph(inv, store)
    assert store.get_node("copybook:CPYA") is not None


def test_includes_copybook_edge(store):
    inv = WorkspaceInventory(
        workspace_path="/ws",
        programs=[_pgm("/ws/PGMA.cbl")],
        copybooks=[_cpy("/ws/CPYA.cpy")],
        copybook_refs=[
            CopybookRef(member_name="CPYA", source_file="/ws/PGMA.cbl",
                        line=10, resolved_path="/ws/CPYA.cpy", is_resolved=True)
        ],
    )
    build_graph(inv, store)
    edges = store.get_outgoing("program:PGMA", "INCLUDES_COPYBOOK")
    assert len(edges) == 1
    assert edges[0].to_id == "copybook:CPYA"


def test_calls_program_edge(store):
    inv = WorkspaceInventory(
        workspace_path="/ws",
        programs=[_pgm("/ws/PGMA.cbl")],
        dependency_refs=[
            DependencyRef(kind=DependencyKind.CALL, source_file="/ws/PGMA.cbl",
                          line=5, target="SUBRTN", target_is_literal=True)
        ],
    )
    build_graph(inv, store)
    edges = store.get_outgoing("program:PGMA", "CALLS_PROGRAM")
    assert len(edges) == 1
    assert edges[0].to_id == "program:SUBRTN"


def test_dynamic_call_not_graphed(store):
    inv = WorkspaceInventory(
        workspace_path="/ws",
        programs=[_pgm("/ws/PGMA.cbl")],
        dependency_refs=[
            DependencyRef(kind=DependencyKind.CALL, source_file="/ws/PGMA.cbl",
                          line=5, target="WS-PGM-VAR", target_is_literal=False)
        ],
    )
    build_graph(inv, store)
    assert store.edge_count("CALLS_PROGRAM") == 0


def test_cics_link_edge(store):
    inv = WorkspaceInventory(
        workspace_path="/ws",
        programs=[_pgm("/ws/PGMA.cbl")],
        dependency_refs=[
            DependencyRef(kind=DependencyKind.EXEC_CICS, source_file="/ws/PGMA.cbl",
                          line=20, target="LINK", detail="PGMB")
        ],
    )
    build_graph(inv, store)
    edges = store.get_outgoing("program:PGMA", "CICS_LINKS_PROGRAM")
    assert edges[0].to_id == "program:PGMB"


def test_sql_reads_table_edge(store):
    inv = WorkspaceInventory(
        workspace_path="/ws",
        programs=[_pgm("/ws/PGMA.cbl")],
        dependency_refs=[
            DependencyRef(kind=DependencyKind.EXEC_SQL, source_file="/ws/PGMA.cbl",
                          line=30, target="SELECT", detail="CUSTOMER")
        ],
    )
    build_graph(inv, store)
    edges = store.get_outgoing("program:PGMA", "READS_TABLE")
    assert edges[0].to_id == "db2table:CUSTOMER"


def test_sql_writes_table_edge(store):
    inv = WorkspaceInventory(
        workspace_path="/ws",
        programs=[_pgm("/ws/PGMA.cbl")],
        dependency_refs=[
            DependencyRef(kind=DependencyKind.EXEC_SQL, source_file="/ws/PGMA.cbl",
                          line=30, target="INSERT", detail="ACCOUNT")
        ],
    )
    build_graph(inv, store)
    assert store.edge_count("WRITES_TABLE") == 1


def test_jcl_job_and_step_nodes(store):
    inv = WorkspaceInventory(
        workspace_path="/ws",
        jcl_jobs=[_jcl("/ws/MYJOB.jcl")],
        jcl_refs=[
            JclRef(kind=JclRefKind.JOB, source_file="/ws/MYJOB.jcl", line=1,
                   name="MYJOB", target=None),
            JclRef(kind=JclRefKind.EXEC_PGM, source_file="/ws/MYJOB.jcl", line=2,
                   name="STEP1", target="PGMA"),
        ],
    )
    build_graph(inv, store)
    assert store.get_node("jcl_job:MYJOB") is not None
    assert store.get_node("jcl_step:MYJOB:STEP1") is not None
    assert store.edge_count("HAS_STEP") == 1
    assert store.edge_count("EXECUTES_PROGRAM") == 1


def test_sql_include_does_not_create_table_node(store):
    """EXEC SQL INCLUDE is a copybook ref — must not pollute the db2table namespace."""
    inv = WorkspaceInventory(
        workspace_path="/ws",
        programs=[_pgm("/ws/BANKDATA.cbl")],
        dependency_refs=[
            DependencyRef(kind=DependencyKind.EXEC_SQL, source_file="/ws/BANKDATA.cbl",
                          line=53, target="INCLUDE", detail="CUSTDB2")
        ],
    )
    build_graph(inv, store)
    assert store.get_node("db2table:CUSTDB2") is None
    assert store.edge_count("ACCESSES_TABLE") == 0


def test_jcl_exec_program_links_to_program_node(store):
    inv = WorkspaceInventory(
        workspace_path="/ws",
        programs=[_pgm("/ws/PGMA.cbl")],
        jcl_jobs=[_jcl("/ws/MYJOB.jcl")],
        jcl_refs=[
            JclRef(kind=JclRefKind.JOB, source_file="/ws/MYJOB.jcl", line=1,
                   name="MYJOB", target=None),
            JclRef(kind=JclRefKind.EXEC_PGM, source_file="/ws/MYJOB.jcl", line=2,
                   name="STEP1", target="PGMA"),
        ],
    )
    build_graph(inv, store)
    step_id = "jcl_step:MYJOB:STEP1"
    edges = store.get_outgoing(step_id, "EXECUTES_PROGRAM")
    assert edges[0].to_id == "program:PGMA"
