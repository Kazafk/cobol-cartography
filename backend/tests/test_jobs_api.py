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
async def test_job_programs_not_found(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/jobs/GHOST/programs")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_job_programs_single_step(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    (tmp_path / "MYJOB.jcl").write_text(
        "//MYJOB  JOB\n"
        "//STEP1  EXEC PGM=PGMA\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/jobs/MYJOB/programs")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_name"] == "MYJOB"
    assert data["total_programs"] == 1
    assert len(data["steps"]) == 1
    assert data["steps"][0]["step_name"] == "STEP1"
    assert data["steps"][0]["program_name"] == "PGMA"
    assert data["steps"][0]["program_path"] is not None


@pytest.mark.asyncio
async def test_job_programs_multiple_steps(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    (tmp_path / "PGMB.cbl").write_text("IDENTIFICATION DIVISION.")
    (tmp_path / "MYJOB.jcl").write_text(
        "//MYJOB  JOB\n"
        "//STEP1  EXEC PGM=PGMA\n"
        "//STEP2  EXEC PGM=PGMB\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/jobs/MYJOB/programs")
    data = resp.json()
    assert data["total_programs"] == 2
    step_names = {s["step_name"] for s in data["steps"]}
    prog_names = {s["program_name"] for s in data["steps"]}
    assert "STEP1" in step_names
    assert "STEP2" in step_names
    assert "PGMA" in prog_names
    assert "PGMB" in prog_names


@pytest.mark.asyncio
async def test_job_programs_stub_program(tmp_path):
    # EXTERN is called by the JCL but not in the workspace — appears as a stub
    (tmp_path / "MYJOB.jcl").write_text(
        "//MYJOB  JOB\n"
        "//STEP1  EXEC PGM=EXTERN\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/jobs/MYJOB/programs")
    data = resp.json()
    assert data["total_programs"] == 1
    step = data["steps"][0]
    assert step["program_name"] == "EXTERN"
    assert step["program_path"] is None  # stub: not found in workspace


@pytest.mark.asyncio
async def test_job_programs_case_insensitive(tmp_path):
    (tmp_path / "PGMA.cbl").write_text("IDENTIFICATION DIVISION.")
    (tmp_path / "MYJOB.jcl").write_text(
        "//MYJOB  JOB\n"
        "//STEP1  EXEC PGM=PGMA\n"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/api/index/workspace", json={"workspacePath": str(tmp_path)})
        resp = await c.get("/api/jobs/myjob/programs")
    assert resp.status_code == 200
    assert resp.json()["job_name"] == "MYJOB"
