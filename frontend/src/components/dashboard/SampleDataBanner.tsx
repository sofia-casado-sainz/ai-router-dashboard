/** Aviso de que las métricas son de ejemplo mientras no haya persistencia ni analítica reales. */
export default function SampleDataBanner() {
  return (
    <div
      role="note"
      className="mb-6 flex items-start gap-3 rounded-xl border border-amber-500/20 bg-amber-500/[0.06] px-4 py-3"
    >
      <svg
        viewBox="0 0 20 20"
        fill="currentColor"
        aria-hidden
        className="mt-0.5 h-4 w-4 shrink-0 text-amber-400"
      >
        <path
          fillRule="evenodd"
          d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM9 9a.75.75 0 0 0 0 1.5h.253a.25.25 0 0 1 .244.304l-.459 2.066A1.75 1.75 0 0 0 10.747 15H11a.75.75 0 0 0 0-1.5h-.253a.25.25 0 0 1-.244-.304l.459-2.066A1.75 1.75 0 0 0 9.253 9H9Z"
          clipRule="evenodd"
        />
      </svg>
      <p className="text-sm text-amber-100/80">
        <span className="font-medium text-amber-200">Datos de ejemplo.</span> Las métricas
        mostradas son simuladas hasta la llegada de persistencia y analítica reales.
      </p>
    </div>
  );
}
