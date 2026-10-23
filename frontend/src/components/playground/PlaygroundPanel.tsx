"use client";

import { usePlaygroundRouter } from "@/hooks/usePlaygroundRouter";
import BackendStatus from "./BackendStatus";
import DecisionHistory from "./DecisionHistory";
import PlaygroundInput from "./PlaygroundInput";

/** Contenedor del Playground: conecta el estado (backend real) con historial y entrada. */
export default function PlaygroundPanel() {
  const { messages, isRouting, sendMessage, retry, reset } = usePlaygroundRouter();

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-white/[0.06] bg-zinc-900/30">
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-white/[0.06] px-4">
        <BackendStatus />
        {messages.length > 0 && (
          <button
            type="button"
            onClick={reset}
            className="rounded-md px-2 py-1 text-xs font-medium text-zinc-400 hover:bg-white/[0.06] hover:text-white"
          >
            Limpiar historial
          </button>
        )}
      </div>

      <DecisionHistory
        messages={messages}
        isRouting={isRouting}
        onSuggestion={sendMessage}
        onRetry={retry}
      />
      <PlaygroundInput onSend={sendMessage} disabled={isRouting} />
    </div>
  );
}
