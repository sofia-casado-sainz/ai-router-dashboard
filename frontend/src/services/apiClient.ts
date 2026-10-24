import { API_PREFIX, API_TIMEOUT_MS, API_URL } from "@/lib/config";

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

/** Extrae un mensaje legible del `detail` de FastAPI (texto o lista de errores de validación 422). */
function parseErrorDetail(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item: { msg?: unknown }) => (typeof item?.msg === "string" ? item.msg : null))
      .filter(Boolean);
    return messages.length > 0 ? messages.join(" · ") : null;
  }
  return null;
}

/** Petición JSON al backend con timeout y errores normalizados como ApiError. */
export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${API_PREFIX}${path}`, {
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
      .then((body: { detail?: unknown }) => parseErrorDetail(body.detail))
      .catch(() => null);
    throw new ApiError(detail ?? `Error del backend (HTTP ${response.status}).`, response.status);
  }

  return response.json() as Promise<T>;
}
