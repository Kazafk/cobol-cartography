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
    logging.basicConfig(
        format="%(message)s",
        level=logging.getLevelName(log_level),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    log = structlog.get_logger()
    log.info("cobol_cartography_starting", version="0.1.0")
    yield
    log.info("cobol_cartography_stopping")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="Cobol Cartography",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    return app


app = create_app()
