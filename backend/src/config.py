from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    ai_mode: str = Field(default="local_strict", alias="AI_MODE")
    allow_external_ai: bool = Field(default=False, alias="ALLOW_EXTERNAL_AI")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    parser_jar_path: str = Field(
        default="../parser/build/libs/parser.jar", alias="PARSER_JAR_PATH"
    )
    graph_backend: str = Field(default="sqlite", alias="GRAPH_BACKEND")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    version: str = Field(default="0.1.0")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
