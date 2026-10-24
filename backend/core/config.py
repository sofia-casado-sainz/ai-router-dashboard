"""Configuración centralizada de la aplicación.

Todo acceso a variables de entorno pasa por `Settings`. Orden de prioridad
(de mayor a menor): variables de entorno, backend/.env, .env de la raíz y
los valores por defecto definidos aquí.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import URL

BACKEND_DIR = Path(__file__).resolve().parent.parent

Environment = Literal["development", "test", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Si un archivo no existe se ignora; el último de la tupla tiene prioridad.
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        # El .env de la raíz también contiene variables del frontend y de Docker.
        extra="ignore",
    )

    app_name: str = "AI Router API"
    app_version: str = "0.1.0"
    environment: Environment = "development"
    log_level: LogLevel = "INFO"

    host: str = "127.0.0.1"
    # 8010 por defecto para no chocar con el 8000.
    port: int = 8010

    api_prefix: str = "/api/v1"

    # Origen del frontend; siempre se permite en CORS.
    frontend_url: str = "http://localhost:3000"
    # Orígenes adicionales permitidos, separados por comas.
    cors_origins: Annotated[list[str], NoDecode] = ["http://127.0.0.1:3000"]

    # PostgreSQL. Si DATABASE_URL está definida, tiene prioridad sobre POSTGRES_*.
    # Comparte las variables POSTGRES_* con docker compose (.env de la raíz).
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_router"
    postgres_user: str = "ai_router"
    postgres_password: str = ""

    # Ejecución de modelos (ADR-0001). Desactivada por defecto: ejecutar modelos
    # cuesta dinero, y POST /api/v1/completions responde 503 mientras esté apagada.
    completions_enabled: bool = False
    # Timeout por defecto de cada ejecución, en segundos.
    completions_timeout_seconds: float = Field(default=60.0, gt=0)

    @field_validator("log_level", mode="before")
    @classmethod
    def _uppercase_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def allowed_origins(self) -> list[str]:
        origins = [self.frontend_url, *self.cors_origins]
        # Sin barra final y sin duplicados, conservando el orden.
        return list(dict.fromkeys(origin.rstrip("/") for origin in origins))

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL para SQLAlchemy con driver asíncrono (asyncpg)."""
        if self.database_url:
            return self.database_url
        url = URL.create(
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password or None,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )
        return url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
