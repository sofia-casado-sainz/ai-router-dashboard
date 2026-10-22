import { cn } from "@/lib/utils";

const SEGMENTS = 10;

function levelColor(value: number) {
  if (value >= 8) return "bg-rose-400";
  if (value >= 5) return "bg-amber-400";
  return "bg-emerald-400";
}

export default function ComplexityMeter({ value }: { value: number }) {
  const color = levelColor(value);

  return (
    <div
      role="meter"
      aria-valuemin={1}
      aria-valuemax={SEGMENTS}
      aria-valuenow={value}
      aria-label="Complejidad"
      className="flex gap-0.5"
    >
      {Array.from({ length: SEGMENTS }, (_, i) => (
        <span
          key={i}
          className={cn("h-1.5 flex-1 rounded-full", i < value ? color : "bg-white/[0.08]")}
        />
      ))}
    </div>
  );
}
