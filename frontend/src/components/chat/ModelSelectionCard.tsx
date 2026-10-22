import { formatCost, formatCompactNumber } from "@/lib/format";
import { getModelStyles } from "@/lib/routing/models";
import { cn } from "@/lib/utils";
import type { RoutingDecision } from "@/types/chat";
import ComplexityMeter from "./ComplexityMeter";

export default function ModelSelectionCard({ decision }: { decision: RoutingDecision }) {
  const { model } = decision;
  const styles = getModelStyles(model.id);

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-white/[0.08] bg-linear-to-br to-zinc-900/80 to-60%",
        styles.accent,
      )}
    >
      {/* Cabecera: modelo elegido */}
      <div className="flex items-start justify-between gap-3 border-b border-white/[0.06] px-4 py-3">
        <div className="min-w-0">
          <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Modelo seleccionado
          </p>
          <div className="mt-1 flex items-center gap-2">
            <span aria-hidden className={cn("h-2 w-2 rounded-full", styles.dot)} />
            <span className="text-base font-semibold text-white">{model.name}</span>
            <span
              className={cn(
                "rounded-md px-1.5 py-0.5 text-[11px] font-medium ring-1 ring-inset",
                styles.badge,
              )}
            >
              {model.provider}
            </span>
          </div>
        </div>
        {decision.isFallback && (
          <span className="shrink-0 rounded-md bg-white/[0.04] px-1.5 py-0.5 text-[11px] text-zinc-400 ring-1 ring-inset ring-white/[0.08]">
            Por defecto
          </span>
        )}
      </div>

      {/* Métricas */}
      <dl className="grid grid-cols-2 divide-x divide-white/[0.06] border-b border-white/[0.06]">
        <div className="px-4 py-3">
          <dt className="text-xs text-zinc-500">Coste estimado</dt>
          <dd className="mt-1 text-sm font-semibold text-white">
            {formatCost(decision.estimatedCost)}
          </dd>
          <dd className="text-[11px] text-zinc-500">
            ~{formatCompactNumber(decision.estimatedTokens)} tokens
          </dd>
        </div>
        <div className="px-4 py-3">
          <dt className="flex items-baseline justify-between text-xs text-zinc-500">
            Complejidad
            <span className="text-sm font-semibold text-white">{decision.complexity}/10</span>
          </dt>
          <dd className="mt-2.5">
            <ComplexityMeter value={decision.complexity} />
          </dd>
        </div>
      </dl>

      {/* Motivo */}
      <div className="px-4 py-3">
        <p className="text-xs text-zinc-500">Motivo</p>
        <p className="mt-1 text-sm text-zinc-200">{decision.reason}</p>
        {decision.matchedKeywords.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {decision.matchedKeywords.map((keyword) => (
              <span
                key={keyword}
                className="rounded bg-white/[0.04] px-1.5 py-0.5 font-mono text-[11px] text-zinc-400 ring-1 ring-inset ring-white/[0.06]"
              >
                {keyword}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
