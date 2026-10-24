from collections.abc import AsyncIterator

import pytest

from domain.completions import (
    CompletionChunk,
    CompletionRequest,
    CompletionResult,
    ProviderCapabilities,
    ProviderHealth,
    ProviderModel,
)
from providers.errors import ProviderNotConfigured
from providers.registry import ProviderRegistry


class StubProvider:
    """Cumple el contrato sin hacer nada; solo sirve para probar el registro."""

    capabilities = ProviderCapabilities()

    def __init__(self, key: str) -> None:
        self.key = key

    async def complete(self, request: CompletionRequest) -> CompletionResult:
        raise NotImplementedError

    def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]:
        raise NotImplementedError

    async def list_models(self) -> list[ProviderModel]:
        raise NotImplementedError

    async def health(self) -> ProviderHealth:
        return ProviderHealth(status="ok")


def test_register_and_get() -> None:
    registry = ProviderRegistry()
    provider = StubProvider("stub")

    registry.register(provider)

    assert registry.get("stub") is provider


def test_list_returns_providers_in_registration_order() -> None:
    registry = ProviderRegistry()
    first, second = StubProvider("a"), StubProvider("b")
    registry.register(first)
    registry.register(second)

    assert registry.list() == (first, second)


def test_list_of_empty_registry() -> None:
    assert ProviderRegistry().list() == ()


def test_duplicate_key_is_rejected() -> None:
    registry = ProviderRegistry()
    registry.register(StubProvider("stub"))

    with pytest.raises(ValueError):
        registry.register(StubProvider("stub"))


def test_unregistered_key_is_not_configured() -> None:
    with pytest.raises(ProviderNotConfigured) as error:
        ProviderRegistry().get("openrouter")

    assert error.value.inference_provider == "openrouter"


def test_object_without_contract_is_rejected() -> None:
    with pytest.raises(TypeError):
        ProviderRegistry().register(object())  # type: ignore[arg-type]
