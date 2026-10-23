/** Un ejemplo por regla del router, para ver decisiones distintas. */
const SUGGESTIONS = [
  "Resume este correo para mi equipo",
  "Diseña una arquitectura para una API",
  "Analiza este bug de producción en TypeScript",
  "Compara tres bases de datos vectoriales",
];

interface PlaygroundEmptyStateProps {
  onSuggestion: (prompt: string) => void;
}

export default function PlaygroundEmptyState({ onSuggestion }: PlaygroundEmptyStateProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 py-10 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-linear-to-br from-indigo-500 to-violet-600 text-xl shadow-lg shadow-indigo-500/20">
        🧭
      </span>
      <h2 className="mt-4 text-lg font-semibold text-white">¿Qué tarea quieres enrutar?</h2>
      <p className="mt-1 max-w-md text-sm text-zinc-400">
        El router analiza la tarea y te muestra qué modelo elegiría, cuánto costaría y por qué. No
        ejecuta el modelo ni genera una respuesta.
      </p>

      <p className="mt-8 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
        Prueba con un ejemplo
      </p>
      <div className="mt-3 grid w-full max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onSuggestion(suggestion)}
            className="rounded-xl border border-white/[0.06] bg-zinc-900/60 px-4 py-3 text-left text-sm text-zinc-300 transition-colors hover:border-white/[0.12] hover:bg-zinc-900 hover:text-white"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
