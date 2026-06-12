import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture(autouse=True)
def reset_state():
    from src.api import indexing as idx
    from src.api import ai
    idx._inventories.clear()
    if idx._graph_store:
        idx._graph_store.clear()
    yield
    idx._inventories.clear()
    if idx._graph_store:
        idx._graph_store.clear()


@pytest.mark.asyncio
async def test_explain_program_not_found(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.post("/api/ai/explain/program", json={"programId": "GHOST"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_explain_program_basic_summary(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("       COPY MYREC.\n")
    (tmp_path / "MYREC.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.post("/api/ai/explain/program", json={"programId": "PGMA"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["program_id"] == "PGMA"
    assert data["ai_mode"] == "local_strict"
    assert data["summary"]["complexity_indicators"]["copybooks_included"] == 1
    assert "PGMA" in data["summary"]["role"]


@pytest.mark.asyncio
async def test_explain_program_sql_business_rules(tmp_path):
    (tmp_path / "PGMA.cbl").write_text(
        "       EXEC SQL SELECT * FROM CUSTOMER END-EXEC.\n"
        "       EXEC SQL INSERT INTO ACCOUNT VALUES(1) END-EXEC.\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.post("/api/ai/explain/program", json={"programId": "PGMA"})
    data = resp.json()
    descriptions = [c["description"] for c in data["business_rule_candidates"]]
    assert any("CUSTOMER" in d for d in descriptions)
    assert any("ACCOUNT" in d for d in descriptions)
    assert all(0 < c["confidence"] <= 1.0 for c in data["business_rule_candidates"])


@pytest.mark.asyncio
async def test_explain_program_no_business_rules_when_excluded(tmp_path):
    (tmp_path / "PGMA.cbl").write_text(
        "       EXEC SQL SELECT * FROM CUSTOMER END-EXEC.\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.post(
            "/api/ai/explain/program",
            json={"programId": "PGMA", "includeBusinessRules": False},
        )
    assert resp.json()["business_rule_candidates"] == []


@pytest.mark.asyncio
async def test_explain_program_uncertainties_always_present(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.post("/api/ai/explain/program", json={"programId": "PGMA"})
    uncertainties = resp.json()["uncertainties"]
    assert len(uncertainties) >= 1
    assert any("dynamique" in u.lower() or "dynamic" in u.lower() for u in uncertainties)


@pytest.mark.asyncio
async def test_explain_program_stub_uncertainty(tmp_path):
    # PGMA calls EXTERN which is not in the workspace (stub node, path=None)
    (tmp_path / "PGMA.cbl").write_text("       CALL 'EXTERN'.\n")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.post("/api/ai/explain/program", json={"programId": "PGMA"})
    data = resp.json()
    assert any("EXTERN" in u for u in data["uncertainties"])
