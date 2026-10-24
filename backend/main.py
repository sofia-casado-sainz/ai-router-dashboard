import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from api.middleware import RequestIdMiddleware
from api.routes import router
from core.config import Settings, get_settings
from core.logging import configure_logging
from core.request_context import REQUEST_ID_HEADER
from database.session import create_engine, create_session_factory
from providers.fake import FakeProvider
from providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


def build_provider_registry() -> ProviderRegistry:
    """Inference providers disponibles (ADR-0001).

    En S2 solo FakeProvider: sin red, sin claves y sin coste. Un proveedor que no
    esté registrado aquí responde como ProviderNotConfigured.
    """
    registry = ProviderRegistry()
    registry.register(FakeProvider())
    return registry


def _operation_id(route: APIRoute) -> str:
    """operationId estable (`get_health`, `route_prompt`) para generar tipos desde OpenAPI."""
    return route.name


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    # El motor no conecta al crearse: la app arranca aunque la base de datos no esté
    # disponible, y solo los endpoints que la usan responden 503.
    engine = create_engine(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        logger.info(
            "Aplicación iniciada",
            extra={"environment": settings.environment, "version": settings.app_version},
        )
        yield
        await engine.dispose()
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
        allow_headers=["Content-Type", REQUEST_ID_HEADER],
        # El navegador solo puede leer las cabeceras que CORS expone.
        expose_headers=[REQUEST_ID_HEADER],
    )
    # Se añade después de CORS para envolverlo: también las respuestas de CORS
    # (p. ej. un preflight) llevan X-Request-ID.
    app.add_middleware(RequestIdMiddleware)

    app.state.settings = settings
    app.state.session_factory = create_session_factory(engine)
    app.state.provider_registry = build_provider_registry()
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
