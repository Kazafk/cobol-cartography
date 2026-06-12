import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture(autouse=True)
def reset_state():
    from src.api import indexing as idx
    idx._inventories.clear()
    if idx._graph_store:
        idx._graph_store.clear()
    yield
    idx._inventories.clear()
    if idx._graph_store:
        idx._graph_store.clear()


@pytest.mark.asyncio
async def test_export_empty_graph(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        # Clear the graph to test truly empty export
        from src.api import graph as g
        g._graph_store.clear()
        resp = await c.get("/api/graph/export")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nodes"] == []
    assert data["links"] == []


@pytest.mark.asyncio
async def test_export_nodes_after_indexing(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("       COPY MYREC.\n")
    (tmp_path / "MYREC.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/graph/export")
    assert resp.status_code == 200
    data = resp.json()
    node_ids = {n["id"] for n in data["nodes"]}
    assert "program:PGMA" in node_ids
    assert "copybook:MYREC" in node_ids


@pytest.mark.asyncio
async def test_export_links_reflect_dependencies(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("       COPY MYREC.\n       CALL 'PGMB'.\n")
    (tmp_path / "PGMB.cbl").write_text("IDENTIFICATION DIVISION.")
    (tmp_path / "MYREC.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/graph/export")
    data = resp.json()
    relations = {(l["source"], l["relation"], l["target"]) for l in data["links"]}
    assert ("program:PGMA", "INCLUDES_COPYBOOK", "copybook:MYREC") in relations
    assert ("program:PGMA", "CALLS_PROGRAM", "program:PGMB") in relations


@pytest.mark.asyncio
async def test_export_node_fields(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/graph/export")
    node = next(n for n in resp.json()["nodes"] if n["id"] == "program:PGMA")
    assert node["kind"] == "program"
    assert node["name"] == "PGMA"
    assert node["path"] is not None
    assert "PGMA" in node["path"]
