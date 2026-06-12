import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture(autouse=True)
def reset_state():
    from src.api import indexing as idx
    from src.api import programs as pgm
    from src.api import impact as imp
    idx._inventories.clear()
    if idx._graph_store:
        idx._graph_store.clear()
    yield
    idx._inventories.clear()
    if idx._graph_store:
        idx._graph_store.clear()


@pytest.mark.asyncio
async def test_copybook_impact_not_found(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/impact/copybook/GHOST")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_copybook_direct_impact(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("       COPY MYCOPY.\n")
    (tmp_path / "PGMB.cbl").write_text("       COPY MYCOPY.\n")
    (tmp_path / "MYCOPY.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/impact/copybook/MYCOPY")
    assert resp.status_code == 200
    data = resp.json()
    assert data["copybook_name"] == "MYCOPY"
    direct_names = {e["name"] for e in data["direct_impacts"]}
    assert direct_names == {"PGMA", "PGMB"}
    assert all(e["depth"] == 1 for e in data["direct_impacts"])
    assert data["total_programs"] == 2
    assert data["indirect_impacts"] == []


@pytest.mark.asyncio
async def test_copybook_indirect_impact_via_call(tmp_path):
    (tmp_path / "DIRECT.cbl").write_text("       COPY MYCOPY.\n")
    (tmp_path / "CALLER.cbl").write_text("       CALL 'DIRECT'.\n")
    (tmp_path / "MYCOPY.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/impact/copybook/MYCOPY")
    data = resp.json()
    assert data["total_programs"] == 2
    indirect_names = {e["name"] for e in data["indirect_impacts"]}
    assert "CALLER" in indirect_names
    indirect_caller = next(e for e in data["indirect_impacts"] if e["name"] == "CALLER")
    assert indirect_caller["depth"] == 2
    assert indirect_caller["via"] == "DIRECT"


@pytest.mark.asyncio
async def test_copybook_impacted_jobs(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("       COPY MYCOPY.\n")
    (tmp_path / "MYCOPY.cpy").write_text("01 FIELD PIC X.")
    (tmp_path / "MYJOB.jcl").write_text(
        "//MYJOB  JOB\n"
        "//STEP1  EXEC PGM=PGMA\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/impact/copybook/MYCOPY")
    data = resp.json()
    assert data["total_jobs"] == 1
    assert any(j["name"] == "MYJOB" for j in data["impacted_jobs"])


@pytest.mark.asyncio
async def test_copybook_no_impacts_when_unused(tmp_path):
    (tmp_path / "MYCOPY.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/impact/copybook/MYCOPY")
    data = resp.json()
    assert data["total_programs"] == 0
    assert data["total_jobs"] == 0
    assert data["direct_impacts"] == []


# ---------------------------------------------------------------------------
# Table impact tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_table_impact_not_found(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/impact/table/GHOST")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_table_impact_readers(tmp_path):
    (tmp_path / "PGMA.cbl").write_text(
        "       EXEC SQL SELECT * FROM CUSTOMER END-EXEC.\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/impact/table/CUSTOMER")
    assert resp.status_code == 200
    data = resp.json()
    assert data["table_name"] == "CUSTOMER"
    assert any(r["name"] == "PGMA" for r in data["readers"])
    assert data["writers"] == []
    assert data["updaters"] == []
    assert data["deleters"] == []


@pytest.mark.asyncio
async def test_table_impact_multiple_access_types(tmp_path):
    (tmp_path / "PGMA.cbl").write_text(
        "       EXEC SQL SELECT * FROM ACCOUNT END-EXEC.\n"
    )
    (tmp_path / "PGMB.cbl").write_text(
        "       EXEC SQL INSERT INTO ACCOUNT VALUES(1) END-EXEC.\n"
    )
    (tmp_path / "PGMC.cbl").write_text(
        "       EXEC SQL UPDATE ACCOUNT SET COL=1 END-EXEC.\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/impact/table/ACCOUNT")
    data = resp.json()
    assert any(r["name"] == "PGMA" for r in data["readers"])
    assert any(r["name"] == "PGMB" for r in data["writers"])
    assert any(r["name"] == "PGMC" for r in data["updaters"])


@pytest.mark.asyncio
async def test_table_impact_associated_jobs(tmp_path):
    (tmp_path / "PGMA.cbl").write_text(
        "       EXEC SQL SELECT * FROM CUSTOMER END-EXEC.\n"
    )
    (tmp_path / "MYJOB.jcl").write_text(
        "//MYJOB  JOB\n"
        "//STEP1  EXEC PGM=PGMA\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/impact/table/CUSTOMER")
    data = resp.json()
    assert any(j["name"] == "MYJOB" for j in data["associated_jobs"])


@pytest.mark.asyncio
async def test_table_impact_no_programs_access(tmp_path):
    # Table appears as a stub via a CALL to an external program that uses it —
    # but let's just insert a stub node manually by indexing a program that
    # references it, then check the table has no readers.
    (tmp_path / "PGMA.cbl").write_text(
        "       EXEC SQL SELECT * FROM CUSTOMER END-EXEC.\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        # ACCOUNT was never accessed
        resp = await c.get("/api/impact/table/ACCOUNT")
    assert resp.status_code == 404
