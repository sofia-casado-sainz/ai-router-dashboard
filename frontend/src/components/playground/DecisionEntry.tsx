import { formatTime } from "@/lib/format";
import type { Message } from "@/types/playground";
import ModelSelectionCard from "./ModelSelectionCard";

interface DecisionEntryProps {
  message: Message;
  onRetry?: (errorId: string) => void;
}

export default function DecisionEntry({ message, onRetry }: DecisionEntryProps) {
  if (message.role === "error") {
    return (
      <div className="flex gap-3">
        <RouterAvatar />
        <div
          role="alert"
          className="flex min-w-0 max-w-[85%] flex-1 flex-col gap-3 rounded-xl border border-rose-500/20 bg-rose-500/[0.06] px-4 py-3 sm:max-w-[75%] sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="min-w-0">
            <p className="text-sm font-medium text-rose-300">No se pudo enrutar la tarea</p>
            <p className="mt-0.5 text-xs text-rose-300/70">{message.content}</p>
          </div>
          {onRetry && (
            <button
              type="button"
              onClick={() => onRetry(message.id)}
              className="shrink-0 self-start rounded-lg bg-rose-500/15 px-3 py-1.5 text-xs font-medium text-rose-200 ring-1 ring-inset ring-rose-500/30 hover:bg-rose-500/25 sm:self-auto"
            >
              Reintentar
            </button>
          )}
        </div>
      </div>
    );
  }

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] sm:max-w-[75%]">
          <p className="mb-1 text-right text-xs font-medium text-zinc-400">
            Tarea <span className="text-zinc-600">· {formatTime(message.createdAt)}</span>
          </p>
          <div className="whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-indigo-500 px-4 py-2.5 text-sm text-white">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <RouterAvatar />
      <div className="min-w-0 max-w-[85%] flex-1 sm:max-w-[75%]">
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-400">
          Decisión del router{" "}
          <span className="normal-case tracking-normal text-zinc-600">
            · {formatTime(message.createdAt)}
          </span>
        </p>
        <ModelSelectionCard decision={message.decision} />
        <p className="mt-3 text-xs text-zinc-500">{message.content}</p>
      </div>
    </div>
  );
}

export function RouterAvatar() {
  return (
    <span
      aria-hidden
      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-linear-to-br from-indigo-500 to-violet-600 text-[11px] font-bold text-white"
    >
      AR
    </span>
  );
}
