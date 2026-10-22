import { API_TIMEOUT_MS, API_URL } from "@/lib/config";
import { MODELS } from "@/lib/routing/models";
import type { AIModel, ModelId, RoutingDecision } from "@/types/chat";

/** Contrato de POST /route tal y como lo devuelve FastAPI (snake_case). */
interface RouteApiResponse {
  selected_model: ModelId;
  complexity: number;
  estimated_cost: number;
  reason: string;
  model_name: string;
  provider: string;
  estimated_tokens: number;
  matched_keywords: string[];
  is_fallback: boolean;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function withTimeout(signal?: AbortSignal) {
  const timeout = AbortSignal.timeout(API_TIMEOUT_MS);
  return signal ? AbortSignal.any([signal, timeout]) : timeout;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers },
      signal: withTimeout(init.signal ?? undefined),
    });
  } catch (error) {
    // La cancelación explícita (p. ej. al desmontar) se propaga tal cual.
    if (init.signal?.aborted) throw error;
    if (error instanceof DOMException && error.name === "TimeoutError") {
      throw new ApiError("El backend ha tardado demasiado en responder.");
    }
    throw new ApiError(`No se pudo conectar con el backend (${API_URL}).`);
  }

  if (!response.ok) {
    const detail = await response
      .json()
      .then((body: { detail?: unknown }) =>
        typeof body.detail === "string" ? body.detail : null,
      )
      .catch(() => null);
    throw new ApiError(detail ?? `Error del backend (HTTP ${response.status}).`, response.status);
  }

  return response.json() as Promise<T>;
}

function toAIModel(data: RouteApiResponse): AIModel {
  const known = MODELS[data.selected_model];
  return {
    id: data.selected_model,
    name: data.model_name,
    provider: data.provider,
    pricePer1kTokens: known?.pricePer1kTokens ?? 0,
    tagline: known?.tagline ?? "",
  };
}

/** Envía el prompt al router del backend y devuelve la decisión tipada. */
export async function routePrompt(prompt: string, signal?: AbortSignal): Promise<RoutingDecision> {
  const data = await request<RouteApiResponse>("/route", {
    method: "POST",
    body: JSON.stringify({ prompt }),
    signal,
  });

  return {
    model: toAIModel(data),
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
    const data = await request<{ status: string }>("/health", { signal });
    return data.status === "ok";
  } catch {
    return false;
  }
}
