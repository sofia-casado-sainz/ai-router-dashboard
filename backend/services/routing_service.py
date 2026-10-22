"""Capa de servicio: orquesta el enrutado y adapta el resultado al contrato de la API.

Aquí se añadirán más adelante la llamada real al modelo, la persistencia
del consumo y las métricas, sin tocar las rutas ni el selector.
"""

from router.model_selector import select_model
from schemas.route_request import RouteResponse


def route_prompt(prompt: str) -> RouteResponse:
    decision = select_model(prompt)
    return RouteResponse(
        selected_model=decision.model.id,
        complexity=decision.complexity,
        estimated_cost=decision.estimated_cost,
        reason=decision.reason,
        model_name=decision.model.name,
        provider=decision.model.provider,
        estimated_tokens=decision.estimated_tokens,
        matched_keywords=decision.matched_keywords,
        is_fallback=decision.is_fallback,
    )
