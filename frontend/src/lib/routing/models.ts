import type { AIModel, ModelId } from "@/types/chat";

/** Catálogo simulado de modelos. Precios ficticios, solo para la demo. */
export const MODELS: Record<ModelId, AIModel> = {
  "claude-sonnet": {
    id: "claude-sonnet",
    name: "Claude Sonnet",
    provider: "Anthropic",
    pricePer1kTokens: 0.015,
    tagline: "Razonamiento profundo y arquitectura",
  },
  gemini: {
    id: "gemini",
    name: "Gemini",
    provider: "Google",
    pricePer1kTokens: 0.005,
    tagline: "Investigación y contexto largo",
  },
  gpt: {
    id: "gpt",
    name: "GPT",
    provider: "OpenAI",
    pricePer1kTokens: 0.01,
    tagline: "Código y propósito general",
  },
  deepseek: {
    id: "deepseek",
    name: "DeepSeek",
    provider: "DeepSeek",
    pricePer1kTokens: 0.001,
    tagline: "Tareas cortas al mínimo coste",
  },
};

/** Clases de Tailwind por modelo (literales para que Tailwind las detecte). */
export const MODEL_STYLES: Record<ModelId, { dot: string; badge: string; accent: string }> = {
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
