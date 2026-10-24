import socket
from decimal import Decimal

import pytest

from domain.completions import CompletionRequest, Message
from providers.errors import ProviderUnavailable
from providers.fake import CHARS_PER_TOKEN, FakeProvider

pytestmark = pytest.mark.anyio


def make_request(prompt: str = "Resume este correo para mi equipo", **overrides: object):
    fields: dict = {
        "provider_model_id": "fake/model",
        "messages": [Message("user", prompt)],
        "max_output_tokens": 200,
    }
    return CompletionRequest(**(fields | overrides))


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cualquier intento de abrir una conexión hace fallar el test."""

    def blocked(*args: object, **kwargs: object) -> None:
        raise AssertionError("FakeProvider no debe usar la red")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


async def test_same_request_gives_same_result(no_network: None) -> None:
    provider = FakeProvider()

    first = await provider.complete(make_request())
    second = await provider.complete(make_request())

    assert first == second


async def test_different_prompts_give_different_results(no_network: None) -> None:
    provider = FakeProvider()

    first = await provider.complete(make_request("Hola"))
    second = await provider.complete(make_request("Adiós"))

    assert first.content != second.content
    assert first.provider_request_id != second.provider_request_id


async def test_result_is_simulated_and_free(no_network: None) -> None:
    result = await FakeProvider().complete(make_request())

    assert result.content.startswith("[Respuesta simulada de fake/model]")
    assert result.inference_provider == "fake"
    assert result.provider_model_id == "fake/model"
    assert result.finish_reason == "stop"
    assert (result.cost.amount, result.cost.currency, result.cost.source) == (
        Decimal("0"),
        "USD",
        "reported",
    )


async def test_usage_is_derived_from_text_length(no_network: None) -> None:
    prompt = "x" * 40
    result = await FakeProvider().complete(make_request(prompt))

    assert result.usage.input_tokens == 40 // CHARS_PER_TOKEN
    assert result.usage.output_tokens == -(-len(result.content) // CHARS_PER_TOKEN)
    assert result.usage.source == "reported"


async def test_output_is_truncated_to_max_tokens(no_network: None) -> None:
    result = await FakeProvider().complete(make_request(max_output_tokens=5))

    assert result.finish_reason == "length"
    assert len(result.content) == 5 * CHARS_PER_TOKEN
    assert result.usage.output_tokens == 5


async def test_configured_error_is_raised() -> None:
    error = ProviderUnavailable("caído", inference_provider="fake")

    with pytest.raises(ProviderUnavailable) as raised:
        await FakeProvider(error=error).complete(make_request())

    assert raised.value is error


async def test_custom_key() -> None:
    result = await FakeProvider(key="demo").complete(make_request())

    assert result.inference_provider == "demo"


async def test_health_is_ok(no_network: None) -> None:
    health = await FakeProvider().health()

    assert health.status == "ok"


async def test_stream_and_list_models_are_not_implemented() -> None:
    provider = FakeProvider()

    with pytest.raises(NotImplementedError):
        provider.stream(make_request())
    with pytest.raises(NotImplementedError):
        await provider.list_models()
