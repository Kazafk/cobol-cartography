import json
import sqlite3
from dataclasses import dataclass, field


@dataclass
class Node:
    id: str
    kind: str
    name: str
    path: str | None = None
    properties: dict = field(default_factory=dict)


@dataclass
class Edge:
    from_id: str
    to_id: str
    relation: str
    confidence: float = 1.0
    properties: dict = field(default_factory=dict)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id       TEXT PRIMARY KEY,
    kind     TEXT NOT NULL,
    name     TEXT NOT NULL,
    path     TEXT,
    props    TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS edges (
    from_id    TEXT NOT NULL,
    to_id      TEXT NOT NULL,
    relation   TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    props      TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (from_id, to_id, relation)
);
CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
CREATE INDEX IF NOT EXISTS idx_edges_to   ON edges(to_id);
CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
"""


class GraphStore:
    def __init__(self, db_path: str = ":memory:"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def upsert_node(self, node: Node) -> None:
        self._conn.execute(
            """
            INSERT INTO nodes (id, kind, name, path, props)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                kind=excluded.kind, name=excluded.name,
                path=COALESCE(excluded.path, nodes.path),
                props=excluded.props
            """,
            (node.id, node.kind, node.name, node.path, json.dumps(node.properties)),
        )
        self._conn.commit()

    def upsert_edge(self, edge: Edge) -> None:
        self._conn.execute(
            """
            INSERT INTO edges (from_id, to_id, relation, confidence, props)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(from_id, to_id, relation) DO UPDATE SET
                confidence=excluded.confidence, props=excluded.props
            """,
            (edge.from_id, edge.to_id, edge.relation, edge.confidence, json.dumps(edge.properties)),
        )
        self._conn.commit()

    def get_node(self, node_id: str) -> Node | None:
        row = self._conn.execute(
            "SELECT id, kind, name, path, props FROM nodes WHERE id=?", (node_id,)
        ).fetchone()
        return _row_to_node(row) if row else None

    def find_node_by_name(self, name: str, kind: str | None = None) -> Node | None:
        if kind:
            row = self._conn.execute(
                "SELECT id, kind, name, path, props FROM nodes WHERE name=? AND kind=? LIMIT 1",
                (name, kind),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT id, kind, name, path, props FROM nodes WHERE name=? LIMIT 1", (name,)
            ).fetchone()
        return _row_to_node(row) if row else None

    def get_outgoing(self, node_id: str, relation: str | None = None) -> list[Edge]:
        if relation:
            rows = self._conn.execute(
                "SELECT from_id, to_id, relation, confidence, props FROM edges WHERE from_id=? AND relation=?",
                (node_id, relation),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT from_id, to_id, relation, confidence, props FROM edges WHERE from_id=?",
                (node_id,),
            ).fetchall()
        return [_row_to_edge(r) for r in rows]

    def get_incoming(self, node_id: str, relation: str | None = None) -> list[Edge]:
        if relation:
            rows = self._conn.execute(
                "SELECT from_id, to_id, relation, confidence, props FROM edges WHERE to_id=? AND relation=?",
                (node_id, relation),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT from_id, to_id, relation, confidence, props FROM edges WHERE to_id=?",
                (node_id,),
            ).fetchall()
        return [_row_to_edge(r) for r in rows]

    def list_nodes(self, kind: str) -> list[Node]:
        rows = self._conn.execute(
            "SELECT id, kind, name, path, props FROM nodes WHERE kind=? ORDER BY name",
            (kind,),
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def node_count(self, kind: str | None = None) -> int:
        if kind:
            return self._conn.execute(
                "SELECT COUNT(*) FROM nodes WHERE kind=?", (kind,)
            ).fetchone()[0]
        return self._conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

    def edge_count(self, relation: str | None = None) -> int:
        if relation:
            return self._conn.execute(
                "SELECT COUNT(*) FROM edges WHERE relation=?", (relation,)
            ).fetchone()[0]
        return self._conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    def all_nodes(self) -> list[Node]:
        rows = self._conn.execute(
            "SELECT id, kind, name, path, props FROM nodes ORDER BY kind, name"
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def all_edges(self) -> list[Edge]:
        rows = self._conn.execute(
            "SELECT from_id, to_id, relation, confidence, props FROM edges"
        ).fetchall()
        return [_row_to_edge(r) for r in rows]

    def clear(self) -> None:
        self._conn.executescript("DELETE FROM edges; DELETE FROM nodes;")
        self._conn.commit()


def _row_to_node(row: sqlite3.Row) -> Node:
    return Node(
        id=row["id"],
        kind=row["kind"],
        name=row["name"],
        path=row["path"],
        properties=json.loads(row["props"]),
    )


def _row_to_edge(row: sqlite3.Row) -> Edge:
    return Edge(
        from_id=row["from_id"],
        to_id=row["to_id"],
        relation=row["relation"],
        confidence=row["confidence"],
        properties=json.loads(row["props"]),
    )
