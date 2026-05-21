import structlog
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import get_settings
from .api.health import router as health_router


def configure_logging(log_level: str) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    log = structlog.get_logger()
    log.info("cobol_cartography_starting", version=settings.version, ai_mode=settings.ai_mode)
    yield
    log.info("cobol_cartography_stopping")


def create_app() -> FastAPI:
    app = FastAPI(
        title="COBOL Cartography",
        version="0.1.0",
        description="COBOL portfolio analysis backend",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    return app


app = create_app()
