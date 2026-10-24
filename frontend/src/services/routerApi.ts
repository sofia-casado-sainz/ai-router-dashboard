import type { HealthResponse, RouteRequest, RouteResponse } from "@/types/api";
import type { RoutingDecision } from "@/types/playground";
import { request } from "./apiClient";

export { ApiError } from "./apiClient";

/** Envía el prompt al router del backend y devuelve la decisión tipada. */
export async function routePrompt(prompt: string, signal?: AbortSignal): Promise<RoutingDecision> {
  const body: RouteRequest = { prompt };
  const data = await request<RouteResponse>("/route", {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });

  return {
    model: { id: data.selected_model, name: data.model_name, provider: data.provider },
    reason: data.reason,
    matchedKeywords: data.matched_keywords,
    complexity: data.complexity,
    estimatedTokens: data.estimated_tokens,
    estimatedCost: data.estimated_cost,
    isFallback: data.is_fallback,
  };
}

/** Devuelve true si GET /health responde correctamente. */
export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const data = await request<HealthResponse>("/health", { signal });
    return data.status === "ok";
  } catch {
    return false;
  }
}
