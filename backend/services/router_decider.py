"""Adaptador de la Decision Layer: expone el router como puerto Decider (ADR-0001).

Reutiliza route_prompt(), así que la decisión es exactamente la misma que devuelve
POST /api/v1/route.
"""

from __future__ import annotations

from domain.execution import Decision
from schemas.route_request import RouteResponse
from services.routing_service import route_prompt


class RouterDecider:
    def decide(self, prompt: str) -> Decision[RouteResponse]:
        response = route_prompt(prompt)
        return Decision(model_id=str(response.selected_model), details=response)
