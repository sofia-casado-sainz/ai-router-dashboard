export interface NavItem {
  label: string;
  href: string;
  icon: string;
  /** Sprint previsto (p. ej. "S1") si la funcionalidad aún no está implementada. */
  sprint?: string;
}

export type TrendDirection = "up" | "down";

export interface Trend {
  /** Variación porcentual respecto al periodo anterior (p. ej. 12.4 = +12,4 %). */
  change: number;
  /** Dirección en la que la variación se considera positiva para el negocio. */
  goodWhen: TrendDirection;
}

export interface DashboardMetrics {
  period: string;
  tokensUsed: { value: number; trend: Trend };
  totalCost: { value: number; currency: string; trend: Trend };
  /** `share`: porcentaje de los tokens consumidos por el modelo. */
  topModel: { name: string; provider: string; share: number };
  /** Ahorro = coste de la línea base − coste total. */
  savings: { value: number; currency: string; baseline: SavingsBaseline };
}

/** Coste hipotético si todas las peticiones hubieran usado un único modelo. */
export interface SavingsBaseline {
  model: string;
  cost: number;
}
