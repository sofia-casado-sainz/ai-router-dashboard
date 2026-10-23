import { formatCompactNumber, formatCurrency, formatPercent } from "@/lib/format";
import type { DashboardMetrics } from "@/types";
import MetricCard, { type MetricCardProps } from "./MetricCard";

export default function MetricsGrid({ metrics }: { metrics: DashboardMetrics }) {
  const { savings, totalCost } = metrics;

  const cards: MetricCardProps[] = [
    {
      label: "Tokens consumidos",
      value: formatCompactNumber(metrics.tokensUsed.value),
      icon: "⚡",
      trend: metrics.tokensUsed.trend,
      description: "vs. periodo anterior",
    },
    {
      label: "Coste estimado",
      value: formatCurrency(totalCost.value, totalCost.currency),
      icon: "💶",
      trend: totalCost.trend,
      description: "vs. periodo anterior",
    },
    {
      label: "Modelo más usado",
      value: metrics.topModel.name,
      icon: "🤖",
      description: `${metrics.topModel.provider} · ${formatPercent(metrics.topModel.share)} de los tokens`,
    },
    {
      label: "Ahorro estimado",
      value: formatCurrency(savings.value, savings.currency),
      icon: "💰",
      description: "frente al modelo de referencia",
      hint: `Modelo de referencia: ${savings.baseline.model}`,
    },
  ];

  return (
    <section aria-label="Métricas principales">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <MetricCard key={card.label} {...card} />
        ))}
      </div>
      <p className="mt-4 text-xs text-zinc-500">
        <span className="font-medium text-zinc-400">Cómo se calcula el ahorro:</span> coste que
        habrían tenido las mismas peticiones usando siempre el modelo de referencia (
        {formatCurrency(savings.baseline.cost, savings.currency)}), menos el coste estimado con el
        reparto del router (
        {formatCurrency(totalCost.value, totalCost.currency)}). Costes estimados con precios
        simulados.
      </p>
    </section>
  );
}
