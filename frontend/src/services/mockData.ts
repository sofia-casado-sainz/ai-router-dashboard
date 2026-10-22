import type { DashboardMetrics } from "@/types";

export const MOCK_DASHBOARD_METRICS: DashboardMetrics = {
  period: "Últimos 30 días",
  tokensUsed: {
    value: 12_480_000,
    trend: { change: 18.2, goodWhen: "up" },
  },
  totalCost: {
    value: 248.32,
    currency: "EUR",
    trend: { change: -6.4, goodWhen: "down" },
  },
  topModel: {
    name: "Claude Haiku 5.5",
    provider: "Anthropic",
    share: 42,
  },
  savings: {
    value: 1120.5,
    currency: "EUR",
    trend: { change: 23.1, goodWhen: "up" },
  },
};
