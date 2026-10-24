from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from domain.completions import (
    MAX_OUTPUT_TOKENS_LIMIT,
    CompletionRequest,
    Cost,
    Message,
    Usage,
)

MESSAGES = [Message("user", "Hola")]


def make_request(**overrides: object) -> CompletionRequest:
    fields: dict = {"provider_model_id": "fake/model", "messages": MESSAGES, "max_output_tokens": 100}
    return CompletionRequest(**(fields | overrides))


def test_request_stores_messages_as_tuple() -> None:
    request = make_request()

    assert request.messages == (Message("user", "Hola"),)


def test_request_is_immutable() -> None:
    request = make_request()

    with pytest.raises(FrozenInstanceError):
        request.max_output_tokens = 5  # type: ignore[misc]


@pytest.mark.parametrize(
    "overrides",
    [
        {"provider_model_id": ""},
        {"messages": []},
        {"max_output_tokens": 0},
        {"max_output_tokens": MAX_OUTPUT_TOKENS_LIMIT + 1},
        {"temperature": -0.1},
        {"temperature": 2.1},
        {"timeout": 0},
    ],
)
def test_request_rejects_invalid_values(overrides: dict) -> None:
    with pytest.raises(ValueError):
        make_request(**overrides)


def test_request_accepts_the_token_limit() -> None:
    assert make_request(max_output_tokens=MAX_OUTPUT_TOKENS_LIMIT).max_output_tokens == (
        MAX_OUTPUT_TOKENS_LIMIT
    )


def test_usage_allows_unreported_tokens() -> None:
    usage = Usage(input_tokens=None, output_tokens=None, source="reported")

    assert usage.input_tokens is None


def test_usage_rejects_negative_tokens() -> None:
    with pytest.raises(ValueError):
        Usage(input_tokens=-1, output_tokens=0, source="estimated")


@pytest.mark.parametrize("currency", ["usd", "US", "EURO"])
def test_cost_requires_iso_currency(currency: str) -> None:
    with pytest.raises(ValueError):
        Cost(amount=Decimal("0"), currency=currency, source="reported")


def test_cost_rejects_negative_amount() -> None:
    with pytest.raises(ValueError):
        Cost(amount=Decimal("-0.01"), currency="USD", source="reported")
