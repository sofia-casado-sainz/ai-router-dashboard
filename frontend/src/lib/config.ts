/** URL base del backend FastAPI. Se puede sobrescribir en .env.local. */
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8010").replace(
  /\/+$/,
  "",
);

/** Prefijo de la versión de la API (debe coincidir con `api_prefix` del backend). */
export const API_PREFIX = "/api/v1";

/** Tiempo máximo de espera de una petición al backend (ms). */
export const API_TIMEOUT_MS = 15_000;

/** Modelo de referencia con el que se compara el ahorro del router (línea base). */
export const BASELINE_MODEL_NAME = "Claude Sonnet";
