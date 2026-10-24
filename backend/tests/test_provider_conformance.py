"""Contrato que debe cumplir cualquier InferenceProvider (ADR-0001).

Para comprobar un proveedor nuevo, basta con añadirlo a PROVIDERS.
"""

from typing import get_args

import pytest

from domain.completions import (
    CompletionRequest,
    CompletionResult,
    CostSource,
    FinishReason,
    HealthStatus,
    Message,
    ProviderCapabilities,
    ProviderHealth,
    UsageSource,
)
from providers.base import InferenceProvider
from providers.fake import FakeProvider

PROVIDERS = [FakeProvider()]

REQUEST = CompletionRequest(
    provider_model_id="conformance/model",
    messages=[Message("system", "Responde en español."), Message("user", "Hola")],
    max_output_tokens=64,
)


@pytest.fixture(params=PROVIDERS, ids=lambda provider: provider.key)
def provider(request: pytest.FixtureRequest) -> InferenceProvider:
    return request.param


class IncompleteProvider:
    key = "incomplete"

    async def complete(self, request: object) -> object:
        raise NotImplementedError


def test_object_without_full_contract_is_not_a_provider() -> None:
    assert not isinstance(IncompleteProvider(), InferenceProvider)


def test_satisfies_the_interface(provider: InferenceProvider) -> None:
    assert isinstance(provider, InferenceProvider)
    assert isinstance(provider.key, str) and provider.key
    assert isinstance(provider.capabilities, ProviderCapabilities)


@pytest.mark.anyio
async def test_complete_returns_normalized_result(provider: InferenceProvider) -> None:
    result = await provider.complete(REQUEST)

    assert isinstance(result, CompletionResult)
    assert result.inference_provider == provider.key
    assert result.provider_model_id
    assert result.finish_reason in get_args(FinishReason)
    assert result.usage.source in get_args(UsageSource)
    assert result.cost.source in get_args(CostSource)
    if result.usage.output_tokens is not None:
        assert result.usage.output_tokens <= REQUEST.max_output_tokens


@pytest.mark.anyio
async def test_health_returns_status_without_tokens(provider: InferenceProvider) -> None:
    health = await provider.health()

    assert isinstance(health, ProviderHealth)
    assert health.status in get_args(HealthStatus)


@pytest.mark.anyio
async def test_unsupported_capabilities_are_explicit(provider: InferenceProvider) -> None:
    if not provider.capabilities.streaming:
        with pytest.raises(NotImplementedError):
            provider.stream(REQUEST)
    if not provider.capabilities.lists_models:
        with pytest.raises(NotImplementedError):
            await provider.list_models()
