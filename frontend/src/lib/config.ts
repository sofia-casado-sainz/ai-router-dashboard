/** URL base del backend FastAPI. Se puede sobrescribir en .env.local. */
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010").replace(
  /\/+$/,
  "",
);

/** Tiempo máximo de espera de una petición al backend (ms). */
export const API_TIMEOUT_MS = 15_000;
