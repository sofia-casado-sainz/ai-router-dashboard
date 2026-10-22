/**
 * Contrato HTTP con el backend (schemas de FastAPI, en snake_case).
 *
 * Fuente de verdad: contracts/openapi.json, exportado desde FastAPI.
 * En el Sprint S1 este archivo se sustituirá por tipos generados a partir de
 * ese OpenAPI; hasta entonces se mantiene a mano y solo aquí.
 */

/** Cuerpo de POST /api/v1/route (operationId `route_prompt`). */
export interface RouteRequest {
  prompt: string;
}

/** Respuesta de POST /api/v1/route (operationId `route_prompt`). */
export interface RouteResponse {
  selected_model: string;
  complexity: number;
  /** Coste estimado en €. */
  estimated_cost: number;
  reason: string;
  model_name: string;
  provider: string;
  estimated_tokens: number;
  matched_keywords: string[];
  is_fallback: boolean;
}

/** Respuesta de GET /api/v1/health (operationId `get_health`). */
export interface HealthResponse {
  status: "ok";
}
