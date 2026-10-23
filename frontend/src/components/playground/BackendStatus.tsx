"use client";

import { useBackendHealth, type BackendStatus as Status } from "@/hooks/useBackendHealth";
import { cn } from "@/lib/utils";

const STATUS_UI: Record<Status, { label: string; dot: string }> = {
  checking: { label: "Conectando…", dot: "bg-zinc-500 animate-pulse" },
  online: { label: "Router activo", dot: "bg-emerald-400" },
  offline: { label: "Backend no disponible", dot: "bg-rose-400" },
};

export default function BackendStatus() {
  const status = useBackendHealth();
  const ui = STATUS_UI[status];

  return (
    <div className="flex items-center gap-2 text-sm" role="status">
      <span className={cn("h-2 w-2 rounded-full", ui.dot)} aria-hidden />
      <span className="font-medium text-zinc-200">{ui.label}</span>
      <span className="hidden text-zinc-500 sm:inline">· selección automática de modelo</span>
    </div>
  );
}
