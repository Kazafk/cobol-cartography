import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture(autouse=True)
def reset_state():
    from src.api import indexing as idx
    from src.api import programs as pgm
    idx._inventories.clear()
    if idx._graph_store:
        idx._graph_store.clear()
    yield
    idx._inventories.clear()
    if idx._graph_store:
        idx._graph_store.clear()


@pytest.mark.asyncio
async def test_list_programs_empty_before_index():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/api/programs")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_programs_after_index(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("       CALL 'SUBRTN'.\n")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/programs")
    assert resp.status_code == 200
    names = {p["name"] for p in resp.json()}
    assert "PGMA" in names


@pytest.mark.asyncio
async def test_index_response_includes_graph_counts(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("       CALL 'SUBRTN'.\n")
    (tmp_path / "CPY.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
    data = resp.json()
    assert data["graphNodes"] > 0
    assert data["graphEdges"] > 0


@pytest.mark.asyncio
async def test_program_dependencies_not_found(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/programs/GHOST/dependencies")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_program_dependencies_calls(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("       CALL 'SUBRTN' USING DATA.\n")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/programs/PGMA/dependencies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["program"]["name"] == "PGMA"
    out_relations = [e["relation"] for e in data["outgoing"]]
    assert "CALLS_PROGRAM" in out_relations


@pytest.mark.asyncio
async def test_program_dependencies_incoming(tmp_path):
    (tmp_path / "CALLER.cbl").write_text("       CALL 'CALLEE' USING DATA.\n")
    (tmp_path / "CALLEE.cbl").write_text("IDENTIFICATION DIVISION.\n")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/programs/CALLEE/dependencies")
    data = resp.json()
    in_names = [e["node"]["name"] for e in data["incoming"]]
    assert "CALLER" in in_names


@pytest.mark.asyncio
async def test_program_dependencies_copybook(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("       COPY MYREC.\n")
    (tmp_path / "MYREC.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/programs/PGMA/dependencies")
    out_relations = [e["relation"] for e in resp.json()["outgoing"]]
    assert "INCLUDES_COPYBOOK" in out_relations


# --- Sheet endpoint ---

@pytest.mark.asyncio
async def test_program_sheet_not_found(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/programs/GHOST/sheet")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_program_sheet_metrics(tmp_path):
    (tmp_path / "PGMA.cbl").write_text(
        "       COPY MYREC.\n"
        "       CALL 'SUBRTN'.\n"
        "       EXEC SQL SELECT * FROM CUSTOMER END-EXEC.\n"
    )
    (tmp_path / "MYREC.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/programs/PGMA/sheet")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "PGMA"
    assert data["metrics"]["copybooks_included"] == 1
    assert data["metrics"]["programs_called"] == 1
    assert data["metrics"]["tables_accessed"] == 1
    assert "MYREC" in data["copybooks"]
    assert any(c["name"] == "SUBRTN" for c in data["calls"])
    assert any(t["name"] == "CUSTOMER" and t["access"] == "READ" for t in data["tables"])


@pytest.mark.asyncio
async def test_program_sheet_called_by(tmp_path):
    (tmp_path / "CALLER.cbl").write_text("       CALL 'CALLEE'.\n")
    (tmp_path / "CALLEE.cbl").write_text("IDENTIFICATION DIVISION.\n")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/programs/CALLEE/sheet")
    data = resp.json()
    assert data["metrics"]["called_by_count"] == 1
    assert any(c["name"] == "CALLER" for c in data["called_by"])


@pytest.mark.asyncio
async def test_program_sheet_executed_by_jcl(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.\n")
    (tmp_path / "MYJOB.jcl").write_text(
        "//MYJOB  JOB\n"
        "//STEP1  EXEC PGM=PGMA\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/programs/PGMA/sheet")
    data = resp.json()
    assert data["metrics"]["executed_by_jobs"] == 1
    assert any(e["job"] == "MYJOB" and e["step"] == "STEP1" for e in data["executed_by"])
