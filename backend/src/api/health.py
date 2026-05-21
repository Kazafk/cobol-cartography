from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..config import Settings, get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


class FeaturesResponse(BaseModel):
    indexing: bool
    graph: bool
    impact_analysis: bool
    ai_explanation: bool


class CapabilitiesResponse(BaseModel):
    ai_mode: str
    features: FeaturesResponse
    parser_version: str
    graph_backend: str


@router.get("/health", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(status="ok", version=settings.version)


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities(
    settings: Annotated[Settings, Depends(get_settings)],
) -> CapabilitiesResponse:
    return CapabilitiesResponse(
        ai_mode=settings.ai_mode,
        features=FeaturesResponse(
            indexing=False,
            graph=False,
            impact_analysis=False,
            ai_explanation=False,
        ),
        parser_version="not_installed",
        graph_backend=settings.graph_backend,
    )
