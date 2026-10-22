import type { RoutingRule } from "@/types/chat";

/**
 * Reglas evaluadas en orden: gana la primera que tenga alguna coincidencia.
 * Las keywords se comparan sin tildes ni mayúsculas (ver normalizeText) y como
 * subcadena, así "compara" cubre comparar/comparativa/comparación.
 */
export const ROUTING_RULES: RoutingRule[] = [
  {
    id: "architecture",
    modelId: "claude-sonnet",
    keywords: ["arquitectura", "diseño sistema", "diseño de sistema", "escalabilidad"],
    reason: "Alta complejidad técnica: requiere razonamiento profundo y visión de sistema.",
    baseComplexity: 8,
  },
  {
    id: "research",
    modelId: "gemini",
    keywords: ["investiga", "búsqueda", "busca", "compara"],
    reason: "Tarea de investigación: prioriza contexto amplio y síntesis de fuentes.",
    baseComplexity: 6,
  },
  {
    id: "code",
    modelId: "gpt",
    keywords: ["código", "programa", "bug", "typescript"],
    reason: "Tarea de programación: modelo optimizado para generar y depurar código.",
    baseComplexity: 7,
  },
  {
    id: "short-text",
    modelId: "deepseek",
    keywords: ["resumen", "resumir", "correo", "email", "texto corto"],
    reason: "Tarea de texto breve: basta un modelo ligero con el menor coste.",
    baseComplexity: 3,
  },
];

export const FALLBACK_RULE: Omit<RoutingRule, "keywords"> = {
  id: "fallback",
  modelId: "gpt",
  reason: "Sin coincidencias específicas: se usa el modelo de propósito general.",
  baseComplexity: 5,
};

/** Minúsculas y sin tildes, para que "Código" y "codigo" coincidan. */
export function normalizeText(text: string) {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}
