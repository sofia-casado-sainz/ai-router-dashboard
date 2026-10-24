"use client";

import { useModelCatalog } from "@/hooks/useModelCatalog";
import { formatCompactNumber, formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { CatalogModel, ModelPrice } from "@/types/models";

const SKELETON_ROWS = 5;

/** Catálogo persistente de modelos (GET /models): estados de carga, error, vacío y tabla. */
export default function ModelCatalog() {
  const { state, reload } = useModelCatalog();

  if (state.status === "error") {
    return (
      <div
        role="alert"
        className="flex flex-col gap-3 rounded-xl border border-rose-500/20 bg-rose-500/[0.06] px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
      >
        <div className="min-w-0">
          <p className="text-sm font-medium text-rose-300">No se pudo cargar el catálogo</p>
          <p className="mt-0.5 text-xs text-rose-300/70">{state.message}</p>
        </div>
        <button
          type="button"
          onClick={reload}
          className="shrink-0 self-start rounded-lg bg-rose-500/15 px-3 py-1.5 text-xs font-medium text-rose-200 ring-1 ring-inset ring-rose-500/30 hover:bg-rose-500/25 sm:self-auto"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (state.status === "ready" && state.models.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-white/[0.08] bg-zinc-900/40 px-6 py-12 text-center">
        <p className="text-sm font-medium text-zinc-200">El catálogo está vacío</p>
        <p className="mt-1 text-sm text-zinc-500">
          Carga los modelos de ejemplo con{" "}
          <code className="font-mono text-zinc-300">python scripts/seed_models.py</code>.
        </p>
      </div>
    );
  }

  const models = state.status === "ready" ? state.models : null;
  const activeCount = models?.filter((model) => model.active).length ?? 0;

  return (
    <section aria-label="Catálogo de modelos" aria-busy={models === null}>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-500">
        <p>
          {models
            ? `${models.length} modelos · ${activeCount} activos para el enrutado`
            : "Cargando catálogo…"}
        </p>
        <p>Precios de ejemplo, por millón de tokens</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-white/[0.06] bg-zinc-900/40">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-white/[0.06] text-xs text-zinc-500">
            <tr>
              <th scope="col" className="px-4 py-3 font-medium">Modelo</th>
              <th scope="col" className="px-4 py-3 font-medium">Proveedor</th>
              <th scope="col" className="px-4 py-3 text-right font-medium">Contexto</th>
              <th scope="col" className="px-4 py-3 text-right font-medium">Entrada</th>
              <th scope="col" className="px-4 py-3 text-right font-medium">Salida</th>
              <th scope="col" className="px-4 py-3 font-medium">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.06]">
            {models
              ? models.map((model) => <ModelRow key={model.id} model={model} />)
              : Array.from({ length: SKELETON_ROWS }, (_, i) => <SkeletonRow key={i} />)}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ModelRow({ model }: { model: CatalogModel }) {
  return (
    <tr className={cn(!model.active && "text-zinc-500")}>
      <td className="px-4 py-3">
        <p className={cn("font-medium", model.active ? "text-white" : "text-zinc-400")}>
          {model.displayName}
        </p>
        <p className="font-mono text-[11px] text-zinc-500">{model.modelKey}</p>
      </td>
      <td className="px-4 py-3">
        <span className="rounded-md bg-white/[0.04] px-1.5 py-0.5 font-mono text-[11px] text-zinc-300 ring-1 ring-inset ring-white/[0.08]">
          {model.provider}
        </span>
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        {formatCompactNumber(model.contextWindow)}
        <span className="text-zinc-500"> tokens</span>
      </td>
      <PriceCell price={model.currentPrice} field="inputCostPerMillion" />
      <PriceCell price={model.currentPrice} field="outputCostPerMillion" />
      <td className="px-4 py-3">
        <span className="inline-flex items-center gap-1.5 text-xs">
          <span
            aria-hidden
            className={cn("h-1.5 w-1.5 rounded-full", model.active ? "bg-emerald-400" : "bg-zinc-600")}
          />
          {model.active ? "Activo" : "Inactivo"}
        </span>
      </td>
    </tr>
  );
}

function PriceCell({
  price,
  field,
}: {
  price: ModelPrice | null;
  field: "inputCostPerMillion" | "outputCostPerMillion";
}) {
  return (
    <td className="px-4 py-3 text-right tabular-nums">
      {price ? (
        formatCurrency(price[field], price.currency)
      ) : (
        <span className="text-zinc-600">Sin precio</span>
      )}
    </td>
  );
}

function SkeletonRow() {
  return (
    <tr aria-hidden>
      {Array.from({ length: 6 }, (_, i) => (
        <td key={i} className="px-4 py-4">
          <span className="block h-3 w-full max-w-24 animate-pulse rounded bg-white/[0.06]" />
        </td>
      ))}
    </tr>
  );
}
