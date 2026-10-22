import type { Metadata } from "next";
import ChatPanel from "@/components/chat/ChatPanel";

export const metadata: Metadata = { title: "Chat Router" };

export default function ChatPage() {
  // Ocupa el alto visible descontando el padding del AppShell (y la Topbar en móvil).
  return (
    <div className="flex h-[calc(100dvh-7.5rem)] flex-col lg:h-[calc(100dvh-5rem)]">
      <div className="mb-4 shrink-0">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Chat Router</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Envía un prompt y el router seleccionará automáticamente el modelo óptimo.
        </p>
      </div>
      <div className="min-h-0 flex-1">
        <ChatPanel />
      </div>
    </div>
  );
}
