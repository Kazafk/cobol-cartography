from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..config import Settings, get_settings

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


class CapabilitiesResponse(BaseModel):
    ai_mode: str
    features: list[str]
    parser_version: str
    graph_backend: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities(
    settings: Annotated[Settings, Depends(get_settings)],
) -> CapabilitiesResponse:
    return CapabilitiesResponse(
        ai_mode=settings.ai_mode,
        features=["indexing", "graph", "impact"],
        parser_version="0.1.0",
        graph_backend=settings.graph_backend,
    )
