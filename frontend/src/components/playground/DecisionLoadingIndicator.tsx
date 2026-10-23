import { RouterAvatar } from "./DecisionEntry";

export default function DecisionLoadingIndicator() {
  return (
    <div className="flex items-center gap-3" role="status">
      <RouterAvatar />
      <div className="flex items-center gap-2 rounded-2xl rounded-bl-md border border-white/[0.06] bg-zinc-900/60 px-4 py-3">
        <span className="flex gap-1" aria-hidden>
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 [animation-delay:-0.3s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400 [animation-delay:-0.15s]" />
          <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-zinc-400" />
        </span>
        <span className="text-xs text-zinc-400">Analizando la tarea y eligiendo modelo…</span>
      </div>
    </div>
  );
}
