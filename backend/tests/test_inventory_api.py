import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture(autouse=True)
def reset_inventory():
    from src.api import indexing as idx_module
    idx_module._inventories.clear()
    yield
    idx_module._inventories.clear()


@pytest.mark.asyncio
async def test_index_workspace_returns_counts(tmp_path):
    (tmp_path / "PGM.cbl").write_text("IDENTIFICATION DIVISION.")
    (tmp_path / "CPY.cpy").write_text("01 FIELD PIC X.")
    (tmp_path / "JOB.jcl").write_text("//JOB JOB")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["programs"] == 1
    assert data["copybooks"] == 1
    assert data["jclJobs"] == 1
    assert data["errors"] == 0
    assert data["jobId"].startswith("idx-")


@pytest.mark.asyncio
async def test_list_programs_after_index(tmp_path):
    (tmp_path / "PGM.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await client.get("/api/inventory/programs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["kind"] == "program"
    assert data[0]["sha256"] != ""


@pytest.mark.asyncio
async def test_list_copybooks_after_index(tmp_path):
    (tmp_path / "CPY.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await client.get("/api/inventory/copybooks")
    assert resp.status_code == 200
    assert resp.json()[0]["kind"] == "copybook"


@pytest.mark.asyncio
async def test_list_jcl_jobs_after_index(tmp_path):
    (tmp_path / "JOB.jcl").write_text("//JOB JOB")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await client.get("/api/inventory/jobs")
    assert resp.status_code == 200
    assert resp.json()[0]["kind"] == "jcl"


@pytest.mark.asyncio
async def test_inventory_404_before_index():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/inventory/programs")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_index_invalid_path_returns_422():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/index/workspace",
            json={"workspacePath": "/nonexistent/path/xyz-does-not-exist"},
        )
    assert resp.status_code == 422


# --- US-011: copybook resolution ---

@pytest.mark.asyncio
async def test_index_reports_unresolved_copybooks(tmp_path):
    (tmp_path / "PGM.cbl").write_text("       COPY MISSING.\n")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
    assert resp.json()["unresolvedCopybooks"] == 1


@pytest.mark.asyncio
async def test_index_reports_zero_unresolved_when_all_resolved(tmp_path):
    (tmp_path / "PGM.cbl").write_text("       COPY PRESENT.\n")
    (tmp_path / "PRESENT.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
    assert resp.json()["unresolvedCopybooks"] == 0


@pytest.mark.asyncio
async def test_copybook_refs_endpoint_returns_all(tmp_path):
    (tmp_path / "PGM.cbl").write_text("       COPY PRESENT.\n       COPY ABSENT.\n")
    (tmp_path / "PRESENT.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await client.get("/api/inventory/copybook-refs")
    data = resp.json()
    assert len(data) == 2
    names = {r["member_name"] for r in data}
    assert names == {"PRESENT", "ABSENT"}


@pytest.mark.asyncio
async def test_copybook_refs_filter_resolved(tmp_path):
    (tmp_path / "PGM.cbl").write_text("       COPY PRESENT.\n       COPY ABSENT.\n")
    (tmp_path / "PRESENT.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resolved = await client.get("/api/inventory/copybook-refs?resolved=true")
        unresolved = await client.get("/api/inventory/copybook-refs?resolved=false")
    assert len(resolved.json()) == 1
    assert resolved.json()[0]["is_resolved"] is True
    assert len(unresolved.json()) == 1
    assert unresolved.json()[0]["member_name"] == "ABSENT"


@pytest.mark.asyncio
async def test_copybook_refs_via_extra_copybook_path(tmp_path):
    pgm_dir = tmp_path / "src"
    pgm_dir.mkdir()
    (pgm_dir / "PGM.cbl").write_text("       COPY EXTERNAL.\n")
    ext_dir = tmp_path / "lib"
    ext_dir.mkdir()
    (ext_dir / "EXTERNAL.cpy").write_text("01 FIELD PIC X.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/index/workspace",
            json={"workspacePath": str(pgm_dir), "copybookPaths": [str(ext_dir)]},
        )
    assert resp.json()["unresolvedCopybooks"] == 0
