export interface ModelStyles {
  dot: string;
  badge: string;
  accent: string;
}

/** Clases de Tailwind por id de modelo (literales para que Tailwind las detecte). Solo presentación. */
const MODEL_STYLES: Record<string, ModelStyles> = {
  "claude-sonnet": {
    dot: "bg-orange-400",
    badge: "bg-orange-500/10 text-orange-300 ring-orange-500/20",
    accent: "from-orange-500/15",
  },
  gemini: {
    dot: "bg-sky-400",
    badge: "bg-sky-500/10 text-sky-300 ring-sky-500/20",
    accent: "from-sky-500/15",
  },
  gpt: {
    dot: "bg-emerald-400",
    badge: "bg-emerald-500/10 text-emerald-300 ring-emerald-500/20",
    accent: "from-emerald-500/15",
  },
  deepseek: {
    dot: "bg-violet-400",
    badge: "bg-violet-500/10 text-violet-300 ring-violet-500/20",
    accent: "from-violet-500/15",
  },
};

const DEFAULT_STYLES: ModelStyles = {
  dot: "bg-zinc-400",
  badge: "bg-white/[0.04] text-zinc-300 ring-white/[0.08]",
  accent: "from-white/[0.04]",
};

/** Estilos del modelo; si el backend devuelve uno nuevo, usa un estilo neutro en lugar de romper. */
export function getModelStyles(modelId: string): ModelStyles {
  return MODEL_STYLES[modelId] ?? DEFAULT_STYLES;
}
