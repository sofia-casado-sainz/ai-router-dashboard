const SUGGESTIONS = [
  "Diseña una arquitectura cloud para un SaaS multi-tenant",
  "Investiga y compara bases de datos vectoriales",
  "Tengo un bug en TypeScript con tipos genéricos",
  "Hazme un resumen de este correo para mi equipo",
];

interface ChatEmptyStateProps {
  onSuggestion: (prompt: string) => void;
}

export default function ChatEmptyState({ onSuggestion }: ChatEmptyStateProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 py-10 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-linear-to-br from-indigo-500 to-violet-600 text-xl shadow-lg shadow-indigo-500/20">
        💬
      </span>
      <h2 className="mt-4 text-lg font-semibold text-white">¿Qué necesitas hoy?</h2>
      <p className="mt-1 max-w-md text-sm text-zinc-400">
        Escribe un prompt y el router elegirá el modelo más adecuado según complejidad y coste.
      </p>

      <div className="mt-8 grid w-full max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
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
