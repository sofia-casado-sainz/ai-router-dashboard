import type { Trend } from "@/types";
import TrendBadge from "./TrendBadge";

export interface MetricCardProps {
  label: string;
  value: string;
  icon: string;
  description?: string;
  /** Aclaración que se muestra como tooltip junto a la descripción. */
  hint?: string;
  trend?: Trend;
}

export default function MetricCard({
  label,
  value,
  icon,
  description,
  hint,
  trend,
}: MetricCardProps) {
  return (
    <div className="group relative overflow-hidden rounded-xl border border-white/[0.06] bg-zinc-900/60 p-5 transition-colors hover:border-white/[0.12]">
      <div
        aria-hidden
        className="pointer-events-none absolute -right-10 -top-10 h-28 w-28 rounded-full bg-indigo-500/10 opacity-0 blur-2xl transition-opacity group-hover:opacity-100"
      />

      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-zinc-400">{label}</p>
        <span
          aria-hidden
          className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/[0.04] text-base ring-1 ring-inset ring-white/[0.06]"
        >
          {icon}
        </span>
      </div>

      <p className="mt-4 truncate text-2xl font-semibold tracking-tight text-white sm:text-[1.75rem]">
        {value}
      </p>

      <div className="mt-3 flex min-h-5 items-center gap-2 text-xs text-zinc-500">
        {trend && <TrendBadge trend={trend} />}
        {description && <span className="truncate">{description}</span>}
        {hint && (
          <span
            role="img"
            tabIndex={0}
            title={hint}
            aria-label={hint}
            className="shrink-0 cursor-help rounded-full text-zinc-500 hover:text-zinc-300 focus:text-zinc-300 focus:outline-none"
          >
            ⓘ
          </span>
        )}
      </div>
    </div>
  );
}
