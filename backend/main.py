import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from api.routes import router
from core.config import Settings, get_settings
from core.logging import configure_logging

logger = logging.getLogger(__name__)


def _operation_id(route: APIRoute) -> str:
    """operationId estable (`get_health`, `route_prompt`) para generar tipos desde OpenAPI."""
    return route.name


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        logger.info(
            "Aplicación iniciada",
            extra={"environment": settings.environment, "version": settings.app_version},
        )
        yield
        logger.info("Aplicación detenida")

    app = FastAPI(
        title=settings.app_name,
        description="Backend del AI Router Dashboard: selección automática de modelos de IA.",
        version=settings.app_version,
        lifespan=lifespan,
        generate_unique_id_function=_operation_id,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    app.include_router(router, prefix=settings.api_prefix)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        # El logging lo configura la aplicación (JSON); uvicorn no debe sobrescribirlo.
        log_config=None,
    )
