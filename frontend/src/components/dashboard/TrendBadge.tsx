import { formatPercent } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Trend } from "@/types";

export default function TrendBadge({ trend }: { trend: Trend }) {
  const direction = trend.change >= 0 ? "up" : "down";
  const isGood = direction === trend.goodWhen;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        isGood
          ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20"
          : "bg-rose-500/10 text-rose-400 ring-rose-500/20",
      )}
    >
      <span aria-hidden>{direction === "up" ? "↑" : "↓"}</span>
      {formatPercent(Math.abs(trend.change))}
    </span>
  );
}
