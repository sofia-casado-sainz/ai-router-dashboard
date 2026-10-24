"""Registro de inference providers: resuelve `inference_provider` → instancia."""

from __future__ import annotations

from providers.base import InferenceProvider
from providers.errors import ProviderNotConfigured


class ProviderRegistry:
    """Un proveedor sin configurar (p. ej. sin clave de API) no se registra, así que
    `get()` lo informa como ProviderNotConfigured sin impedir que arranque la aplicación."""

    def __init__(self) -> None:
        self._providers: dict[str, InferenceProvider] = {}

    def register(self, provider: InferenceProvider) -> None:
        if not isinstance(provider, InferenceProvider):
            raise TypeError(f"{type(provider).__name__} no cumple el contrato InferenceProvider.")
        if provider.key in self._providers:
            raise ValueError(f"Ya hay un inference provider registrado con la clave {provider.key!r}.")
        self._providers[provider.key] = provider

    def get(self, key: str) -> InferenceProvider:
        try:
            return self._providers[key]
        except KeyError:
            raise ProviderNotConfigured(
                f"No hay ningún inference provider configurado con la clave {key!r}.",
                inference_provider=key,
            ) from None

    def list(self) -> tuple[InferenceProvider, ...]:
        """Proveedores registrados, en orden de registro."""
        return tuple(self._providers.values())
