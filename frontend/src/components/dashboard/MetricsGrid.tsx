import { formatCompactNumber, formatCurrency, formatPercent } from "@/lib/format";
import type { DashboardMetrics } from "@/types";
import MetricCard, { type MetricCardProps } from "./MetricCard";

export default function MetricsGrid({ metrics }: { metrics: DashboardMetrics }) {
  const cards: MetricCardProps[] = [
    {
      label: "Tokens consumidos",
      value: formatCompactNumber(metrics.tokensUsed.value),
      icon: "⚡",
      trend: metrics.tokensUsed.trend,
      description: "vs. periodo anterior",
    },
    {
      label: "Coste total",
      value: formatCurrency(metrics.totalCost.value, metrics.totalCost.currency),
      icon: "💶",
      trend: metrics.totalCost.trend,
      description: "vs. periodo anterior",
    },
    {
      label: "Modelo más usado",
      value: metrics.topModel.name,
      icon: "🤖",
      description: `${metrics.topModel.provider} · ${formatPercent(metrics.topModel.share)} de las peticiones`,
    },
    {
      label: "Ahorro generado",
      value: formatCurrency(metrics.savings.value, metrics.savings.currency),
      icon: "💰",
      trend: metrics.savings.trend,
      description: "gracias al enrutado",
    },
  ];

  return (
    <section
      aria-label="Métricas principales"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
    >
      {cards.map((card) => (
        <MetricCard key={card.label} {...card} />
      ))}
    </section>
  );
}
