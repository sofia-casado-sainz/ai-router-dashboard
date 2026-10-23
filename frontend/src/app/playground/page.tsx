import type { Metadata } from "next";
import PlaygroundPanel from "@/components/playground/PlaygroundPanel";

export const metadata: Metadata = { title: "Playground" };

export default function PlaygroundPage() {
  // Ocupa el alto visible descontando el padding del AppShell (y la Topbar en móvil).
  return (
    <div className="flex h-[calc(100dvh-7.5rem)] flex-col lg:h-[calc(100dvh-5rem)]">
      <div className="mb-4 shrink-0">
        <h1 className="text-2xl font-semibold tracking-tight text-white">Playground</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Describe una tarea y observa cómo el router decide qué modelo utilizar.
        </p>
      </div>
      <div className="min-h-0 flex-1">
        <PlaygroundPanel />
      </div>
    </div>
  );
}
