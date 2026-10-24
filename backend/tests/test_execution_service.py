import ast
import asyncio
import logging
import time
from dataclasses import replace
from pathlib import Path

import pytest

from domain.completions import CompletionRequest, CompletionResult, Message
from domain.execution import Decision, ResolvedModel
from providers.errors import (
    ModelNotAvailable,
    ProviderAuthError,
    ProviderBadRequest,
    ProviderError,
    ProviderNotConfigured,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from providers.fake import FakeProvider
from providers.registry import ProviderRegistry
from services.execution_service import ExecutionService

REQUEST = CompletionRequest(
    provider_model_id="fake/model",
    messages=[Message("user", "Resume este correo para mi equipo")],
    max_output_tokens=100,
)


def make_service(*providers: FakeProvider, **kwargs: object) -> ExecutionService:
    registry = ProviderRegistry()
    for provider in providers:
        registry.register(provider)
    return ExecutionService(registry, **kwargs)  # type: ignore[arg-type]


class StubDecider:
    def __init__(self, model_id: str = "gpt") -> None:
        self.model_id = model_id

    def decide(self, prompt: str) -> Decision[dict]:
        return Decision(model_id=self.model_id, details={"prompt": prompt})


class StubResolver:
    def __init__(
        self,
        target: ResolvedModel = ResolvedModel("fake", "gpt-5"),
        error: Exception | None = None,
    ) -> None:
        self.target = target
        self.error = error
        self.requested: list[str] = []

    async def resolve(self, model_id: str) -> ResolvedModel:
        self.requested.append(model_id)
        if self.error is not None:
            raise self.error
        return self.target


class SlowProvider(FakeProvider):
    """Tarda más que el timeout y registra si su llamada se canceló."""

    cancelled = False

    async def complete(self, request: CompletionRequest) -> CompletionResult:
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            self.cancelled = True
            raise
        return await super().complete(request)


class BrokenProvider(FakeProvider):
    """Falla con un error sin tipar, como un fallo de programación en una integración."""

    async def complete(self, request: CompletionRequest) -> CompletionResult:
        raise RuntimeError("respuesta inesperada")


@pytest.mark.anyio
async def test_complete_returns_provider_result_with_measured_latency() -> None:
    ticks = iter([10.0, 10.25])
    service = make_service(FakeProvider(), clock=lambda: next(ticks))

    result = await service.complete("fake", REQUEST)
    expected = await FakeProvider().complete(REQUEST)

    assert result.latency_ms == 250
    assert result.content == expected.content
    assert result.usage == expected.usage
    assert result.cost == expected.cost


@pytest.mark.anyio
async def test_unregistered_provider_is_not_configured() -> None:
    with pytest.raises(ProviderNotConfigured):
        await make_service(FakeProvider()).complete("openrouter", REQUEST)


@pytest.mark.anyio
async def test_request_timeout_is_applied() -> None:
    provider = SlowProvider()
    service = make_service(provider)
    request = replace(REQUEST, timeout=0.05)
    started = time.perf_counter()

    with pytest.raises(ProviderTimeout) as error:
        await service.complete("fake", request)

    assert time.perf_counter() - started < 1
    assert error.value.inference_provider == "fake"
    # La llamada al proveedor se cancela; no sigue ejecutándose en segundo plano.
    assert provider.cancelled


@pytest.mark.anyio
async def test_default_timeout_is_applied_when_request_has_none() -> None:
    service = make_service(FakeProvider(delay_seconds=5), default_timeout_seconds=0.05)

    with pytest.raises(ProviderTimeout):
        await service.complete("fake", REQUEST)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "error",
    [
        ProviderNotConfigured("sin clave"),
        ProviderUnavailable("caído"),
        ProviderTimeout("lento"),
        ProviderRateLimited("límite", retry_after=30),
        ProviderAuthError("clave inválida"),
        ProviderBadRequest("contexto excedido"),
        ModelNotAvailable("modelo retirado"),
    ],
    ids=lambda error: type(error).__name__,
)
async def test_typed_errors_pass_through_unchanged(error: ProviderError) -> None:
    with pytest.raises(type(error)) as raised:
        await make_service(FakeProvider(error=error)).complete("fake", REQUEST)

    assert raised.value is error


@pytest.mark.anyio
async def test_rate_limit_keeps_retry_after() -> None:
    error = ProviderRateLimited("límite", retry_after=30)

    with pytest.raises(ProviderRateLimited) as raised:
        await make_service(FakeProvider(error=error)).complete("fake", REQUEST)

    assert raised.value.retry_after == 30


@pytest.mark.anyio
async def test_unexpected_error_becomes_unavailable(caplog: pytest.LogCaptureFixture) -> None:
    service = make_service(BrokenProvider())

    with caplog.at_level(logging.ERROR, logger="services.execution_service"):
        with pytest.raises(ProviderUnavailable) as raised:
            await service.complete("fake", REQUEST)

    assert isinstance(raised.value.__cause__, RuntimeError)
    assert raised.value.inference_provider == "fake"
    assert any(record.exc_info for record in caplog.records)
    # El prompt no aparece en los logs.
    assert all(REQUEST.messages[0].content not in record.getMessage() for record in caplog.records)


def test_default_timeout_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ExecutionService(ProviderRegistry(), default_timeout_seconds=0)


@pytest.mark.anyio
async def test_execute_decides_resolves_and_completes() -> None:
    resolver = StubResolver()
    service = make_service(FakeProvider(), decider=StubDecider("gpt"), resolver=resolver)

    execution = await service.execute("Resume este correo", max_output_tokens=100)

    assert execution.decision.model_id == "gpt"
    assert execution.decision.details == {"prompt": "Resume este correo"}
    assert resolver.requested == ["gpt"]
    assert execution.result.inference_provider == "fake"
    assert execution.result.provider_model_id == "gpt-5"
    assert execution.result.content.startswith("[Respuesta simulada de gpt-5]")
    assert "Resume este correo" in execution.result.content
    assert execution.result.latency_ms is not None


@pytest.mark.anyio
async def test_execute_passes_request_options() -> None:
    service = make_service(FakeProvider(), decider=StubDecider(), resolver=StubResolver())

    execution = await service.execute("Resume este correo", max_output_tokens=5)

    assert execution.result.finish_reason == "length"
    assert execution.result.usage.output_tokens == 5


@pytest.mark.anyio
async def test_execute_propagates_model_not_available() -> None:
    error = ModelNotAvailable("sin correspondencia")
    service = make_service(FakeProvider(), decider=StubDecider(), resolver=StubResolver(error=error))

    with pytest.raises(ModelNotAvailable) as raised:
        await service.execute("Hola", max_output_tokens=10)

    assert raised.value is error


@pytest.mark.anyio
async def test_execute_with_unregistered_inference_provider_is_not_configured() -> None:
    resolver = StubResolver(ResolvedModel("openrouter", "openai/gpt-5"))
    service = make_service(FakeProvider(), decider=StubDecider(), resolver=resolver)

    with pytest.raises(ProviderNotConfigured):
        await service.execute("Hola", max_output_tokens=10)


@pytest.mark.anyio
async def test_execute_requires_decider_and_resolver() -> None:
    with pytest.raises(RuntimeError):
        await make_service(FakeProvider()).execute("Hola", max_output_tokens=10)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    } | {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}


def test_execution_ports_are_framework_agnostic() -> None:
    """Los puertos de domain/execution.py tampoco dependen de frameworks, HTTP, BD ni del router."""
    source = Path(__file__).resolve().parent.parent / "domain" / "execution.py"
    forbidden = (
        "fastapi",
        "starlette",
        "pydantic",
        "sqlalchemy",
        "httpx",
        "router",
        "api",
        "schemas",
        "database",
        "repositories",
        "services",
    )

    assert not {name for name in _imported_modules(source) if name.split(".")[0] in forbidden}


def test_execution_service_is_framework_agnostic() -> None:
    """ExecutionService no puede depender de frameworks, HTTP, base de datos ni del router."""
    source = Path(__file__).resolve().parent.parent / "services" / "execution_service.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported = {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    } | {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}

    forbidden = ("fastapi", "starlette", "sqlalchemy", "httpx", "router", "api", "database", "repositories")
    assert not {name for name in imported if name.split(".")[0] in forbidden}
