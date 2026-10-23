import Link from "next/link";

interface PlannedFeatureProps {
  icon: string;
  /** Cuándo llegará, p. ej. "Sprint S1" o "Fase futura". */
  availability: string;
  goal: string;
  description: string;
  capabilities: string[];
}

/** Pantalla de una funcionalidad prevista: qué hará, cuándo llegará y qué incluirá. */
export default function PlannedFeature({
  icon,
  availability,
  goal,
  description,
  capabilities,
}: PlannedFeatureProps) {
  return (
    <section className="rounded-xl border border-white/[0.06] bg-zinc-900/40 p-6 sm:p-8">
      <div className="flex flex-wrap items-center gap-3">
        <span
          aria-hidden
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/[0.04] text-xl ring-1 ring-inset ring-white/[0.06]"
        >
          {icon}
        </span>
        <span className="rounded-md bg-indigo-500/10 px-2 py-0.5 text-xs font-medium text-indigo-300 ring-1 ring-inset ring-indigo-500/20">
          Previsto · {availability}
        </span>
        <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-xs font-medium text-zinc-400 ring-1 ring-inset ring-white/[0.08]">
          Aún no implementado
        </span>
      </div>

      <h2 className="mt-5 text-lg font-semibold text-white">{goal}</h2>
      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-400">{description}</p>

      <h3 className="mt-8 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
        Qué incluirá
      </h3>
      <ul className="mt-3 grid gap-2 sm:grid-cols-2">
        {capabilities.map((capability) => (
          <li
            key={capability}
            className="flex items-start gap-2.5 rounded-lg border border-white/[0.06] bg-zinc-900/60 px-3 py-2.5 text-sm text-zinc-300"
          >
            <span aria-hidden className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-400/70" />
            {capability}
          </li>
        ))}
      </ul>

      <p className="mt-8 border-t border-white/[0.06] pt-5 text-sm text-zinc-400">
        Mientras tanto, puedes ver cómo decide el router en el{" "}
        <Link
          href="/playground"
          className="font-medium text-indigo-300 underline-offset-4 hover:text-indigo-200 hover:underline"
        >
          Playground
        </Link>
        .
      </p>
    </section>
  );
}
