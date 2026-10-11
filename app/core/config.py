from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Student Analytics API"
    API_PREFIX: str = "/api/v1"
    # Mount point of the FastMCP ASGI app (see app/mcp/server.py).
    MCP_PATH: str = "/mcp"

    DB_USER: str = "root"
    DB_PASSWORD: str = "CHANGE_ME"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str = "school_db"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
