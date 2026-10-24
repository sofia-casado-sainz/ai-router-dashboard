"""Contrato que debe cumplir cualquier InferenceProvider (ADR-0001)."""

from providers.base import InferenceProvider


class IncompleteProvider:
    key = "incomplete"

    async def complete(self, request: object) -> object:
        raise NotImplementedError


def test_object_without_full_contract_is_not_a_provider() -> None:
    assert not isinstance(IncompleteProvider(), InferenceProvider)
