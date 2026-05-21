from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    ai_mode: str = "local_strict"
    allow_external_ai: bool = False
    log_level: str = "INFO"
    parser_jar_path: str = ""
    graph_backend: str = "sqlite"
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
