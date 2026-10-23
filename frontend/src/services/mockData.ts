import { BASELINE_MODEL_NAME } from "@/lib/config";
import type { DashboardMetrics } from "@/types";

/**
 * Datos de ejemplo, coherentes con el catálogo del backend (router/catalog.py)
 * y sus precios simulados en € por 1.000 tokens:
 *
 *   Modelo         Tokens      Precio   Coste
 *   DeepSeek       4.992.000   0,001     4,99 €
 *   GPT            3.744.000   0,010    37,44 €
 *   Gemini         2.246.400   0,005    11,23 €
 *   Claude Sonnet  1.497.600   0,015    22,46 €
 *   Total         12.480.000            76,13 €
 *
 * Línea base: los mismos tokens con el modelo de referencia (BASELINE_MODEL_NAME,
 * hoy Claude Sonnet a 0,015 €) = 187,20 €.
 * Si cambian los precios del catálogo o el modelo de referencia, hay que recalcular esta tabla.
 */
export const MOCK_DASHBOARD_METRICS: DashboardMetrics = {
  period: "Últimos 30 días",
  tokensUsed: {
    value: 12_480_000,
    trend: { change: 18.2, goodWhen: "up" },
  },
  totalCost: {
    value: 76.13,
    currency: "EUR",
    trend: { change: -6.4, goodWhen: "down" },
  },
  topModel: {
    name: "DeepSeek",
    provider: "DeepSeek",
    share: 40,
  },
  savings: {
    value: 111.07,
    currency: "EUR",
    baseline: { model: BASELINE_MODEL_NAME, cost: 187.2 },
  },
};
