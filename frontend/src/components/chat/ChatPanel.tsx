"use client";

import { useChatRouter } from "@/hooks/useChatRouter";
import ChatHistory from "./ChatHistory";
import ChatInput from "./ChatInput";

/** Contenedor del Chat Router: conecta el estado con historial y entrada. */
export default function ChatPanel() {
  const { messages, isRouting, sendMessage, reset } = useChatRouter();

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-white/[0.06] bg-zinc-900/30">
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-white/[0.06] px-4">
        <div className="flex items-center gap-2 text-sm">
          <span className="h-2 w-2 rounded-full bg-emerald-400" aria-hidden />
          <span className="font-medium text-zinc-200">Router activo</span>
          <span className="hidden text-zinc-500 sm:inline">· selección automática de modelo</span>
        </div>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={reset}
            className="rounded-md px-2 py-1 text-xs font-medium text-zinc-400 hover:bg-white/[0.06] hover:text-white"
          >
            Nueva conversación
          </button>
        )}
      </div>

      <ChatHistory messages={messages} isRouting={isRouting} onSuggestion={sendMessage} />
      <ChatInput onSend={sendMessage} disabled={isRouting} />
    </div>
  );
}
