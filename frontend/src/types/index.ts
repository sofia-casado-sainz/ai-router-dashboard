export interface NavItem {
  label: string;
  href: string;
  icon: string;
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
  topModel: { name: string; provider: string; share: number };
  savings: { value: number; currency: string; trend: Trend };
}
