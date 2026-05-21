import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_capabilities():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["ai_mode"] == "local_strict"
    assert "features" in data
    assert data["features"]["ai_explanation"] is False


@pytest.mark.asyncio
async def test_capabilities_ai_mode_from_config():
    """GET /capabilities must return ai_mode from settings, not hardcoded."""
    import os

    os.environ["AI_MODE"] = "enterprise_controlled"
    # reset cached settings
    import backend.src.config as cfg_module

    cfg_module._settings = None
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/capabilities")
    data = response.json()
    assert data["ai_mode"] == "enterprise_controlled"
    # cleanup
    os.environ.pop("AI_MODE", None)
    cfg_module._settings = None
