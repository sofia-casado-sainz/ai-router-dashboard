"""Errores tipados de los inference providers (ADR-0001).

Cada proveedor traduce sus errores a esta jerarquía. ExecutionService y la API
reaccionan a estos tipos, nunca a los códigos HTTP de un proveedor concreto.
"""

from __future__ import annotations


class ProviderError(Exception):
    def __init__(self, message: str, *, inference_provider: str | None = None) -> None:
        super().__init__(message)
        self.inference_provider = inference_provider


class ProviderNotConfigured(ProviderError):
    """El proveedor no está registrado o le falta configuración (p. ej. la clave de API)."""


class ProviderUnavailable(ProviderError):
    """No se pudo contactar con el proveedor o respondió con un error propio."""


class ProviderTimeout(ProviderError):
    """El proveedor no respondió dentro del timeout."""


class ProviderRateLimited(ProviderError):
    """El proveedor rechazó la petición por límite de uso."""

    def __init__(
        self,
        message: str,
        *,
        inference_provider: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, inference_provider=inference_provider)
        # Segundos sugeridos por el proveedor antes de reintentar, si los indica.
        self.retry_after = retry_after


class ProviderAuthError(ProviderError):
    """Credenciales rechazadas por el proveedor: es un error de configuración."""


class ProviderBadRequest(ProviderError):
    """El proveedor rechazó la petición (p. ej. contexto excedido)."""


class ModelNotAvailable(ProviderError):
    """El modelo pedido no existe o no está disponible en el proveedor."""
