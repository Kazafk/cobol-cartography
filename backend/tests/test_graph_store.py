import pytest

from src.graph.store import Edge, GraphStore, Node


@pytest.fixture
def store():
    return GraphStore()  # in-memory


def test_upsert_and_get_node(store):
    store.upsert_node(Node(id="program:MYPGM", kind="program", name="MYPGM", path="/src/MYPGM.cbl"))
    n = store.get_node("program:MYPGM")
    assert n is not None
    assert n.name == "MYPGM"
    assert n.path == "/src/MYPGM.cbl"


def test_get_node_returns_none_if_missing(store):
    assert store.get_node("program:GHOST") is None


def test_upsert_node_is_idempotent(store):
    store.upsert_node(Node(id="program:MYPGM", kind="program", name="MYPGM"))
    store.upsert_node(Node(id="program:MYPGM", kind="program", name="MYPGM", path="/new/path.cbl"))
    assert store.node_count() == 1
    assert store.get_node("program:MYPGM").path == "/new/path.cbl"


def test_upsert_node_preserves_path_when_null(store):
    store.upsert_node(Node(id="program:X", kind="program", name="X", path="/original.cbl"))
    store.upsert_node(Node(id="program:X", kind="program", name="X", path=None))
    assert store.get_node("program:X").path == "/original.cbl"


def test_upsert_and_query_edges(store):
    store.upsert_node(Node(id="program:A", kind="program", name="A"))
    store.upsert_node(Node(id="program:B", kind="program", name="B"))
    store.upsert_edge(Edge(from_id="program:A", to_id="program:B", relation="CALLS_PROGRAM"))

    out = store.get_outgoing("program:A")
    assert len(out) == 1
    assert out[0].relation == "CALLS_PROGRAM"
    assert out[0].to_id == "program:B"

    inc = store.get_incoming("program:B")
    assert len(inc) == 1
    assert inc[0].from_id == "program:A"


def test_upsert_edge_is_idempotent(store):
    store.upsert_node(Node(id="program:A", kind="program", name="A"))
    store.upsert_node(Node(id="program:B", kind="program", name="B"))
    store.upsert_edge(Edge(from_id="program:A", to_id="program:B", relation="CALLS_PROGRAM"))
    store.upsert_edge(Edge(from_id="program:A", to_id="program:B", relation="CALLS_PROGRAM", confidence=0.9))
    assert store.edge_count() == 1
    assert store.get_outgoing("program:A")[0].confidence == 0.9


def test_filter_outgoing_by_relation(store):
    store.upsert_node(Node(id="program:A", kind="program", name="A"))
    store.upsert_node(Node(id="copybook:C", kind="copybook", name="C"))
    store.upsert_node(Node(id="program:B", kind="program", name="B"))
    store.upsert_edge(Edge(from_id="program:A", to_id="program:B", relation="CALLS_PROGRAM"))
    store.upsert_edge(Edge(from_id="program:A", to_id="copybook:C", relation="INCLUDES_COPYBOOK"))

    calls = store.get_outgoing("program:A", relation="CALLS_PROGRAM")
    assert len(calls) == 1
    assert calls[0].to_id == "program:B"


def test_list_nodes_by_kind(store):
    store.upsert_node(Node(id="program:A", kind="program", name="A"))
    store.upsert_node(Node(id="program:B", kind="program", name="B"))
    store.upsert_node(Node(id="copybook:C", kind="copybook", name="C"))

    programs = store.list_nodes("program")
    assert len(programs) == 2
    assert all(n.kind == "program" for n in programs)


def test_node_and_edge_counts(store):
    store.upsert_node(Node(id="program:A", kind="program", name="A"))
    store.upsert_node(Node(id="program:B", kind="program", name="B"))
    store.upsert_edge(Edge(from_id="program:A", to_id="program:B", relation="CALLS_PROGRAM"))

    assert store.node_count() == 2
    assert store.node_count("program") == 2
    assert store.edge_count() == 1
    assert store.edge_count("CALLS_PROGRAM") == 1


def test_clear(store):
    store.upsert_node(Node(id="program:A", kind="program", name="A"))
    store.upsert_edge(Edge(from_id="program:A", to_id="program:A", relation="SELF"))
    store.clear()
    assert store.node_count() == 0
    assert store.edge_count() == 0


def test_properties_roundtrip(store):
    store.upsert_node(Node(id="program:A", kind="program", name="A",
                           properties={"sha256": "abc123", "size_bytes": 42}))
    n = store.get_node("program:A")
    assert n.properties["sha256"] == "abc123"
    assert n.properties["size_bytes"] == 42
