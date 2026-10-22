import type { DashboardMetrics } from "@/types";
import { MOCK_DASHBOARD_METRICS } from "./mockData";

/**
 * Capa de acceso a datos. Hoy devuelve datos mock; cuando exista backend,
 * solo hay que sustituir la implementación manteniendo la firma.
 */
export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  return MOCK_DASHBOARD_METRICS;
}
