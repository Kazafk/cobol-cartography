import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from .api.ai import router as ai_router
from .api.ai import set_graph_store as ai_set_store
from .api.graph import router as graph_router
from .api.graph import set_graph_store as graph_set_store
from .api.jobs import router as jobs_router
from .api.jobs import set_graph_store as jobs_set_store
from .api.health import router as health_router
from .api.impact import router as impact_router
from .api.impact import set_graph_store as impact_set_store
from .api.indexing import router as indexing_router
from .api.indexing import set_graph_store as indexing_set_store
from .api.programs import router as programs_router
from .api.programs import set_graph_store as programs_set_store
from .config import get_settings
from .graph.store import GraphStore


def configure_logging(log_level: str) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )
    logging.basicConfig(format="%(message)s", level=logging.getLevelName(log_level))


@asynccontextmanager
async def lifespan(app: FastAPI):
    log = structlog.get_logger()
    log.info("cobol_cartography_starting", version="0.1.0")
    yield
    log.info("cobol_cartography_stopping")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    store = GraphStore()  # in-memory SQLite; file-backed path added in a later story
    indexing_set_store(store)
    programs_set_store(store)
    impact_set_store(store)
    ai_set_store(store)
    graph_set_store(store)
    jobs_set_store(store)

    app = FastAPI(title="Cobol Cartography", version="0.1.0", lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(indexing_router)
    app.include_router(programs_router)
    app.include_router(impact_router)
    app.include_router(ai_router)
    app.include_router(graph_router)
    app.include_router(jobs_router)
    return app


app = create_app()
