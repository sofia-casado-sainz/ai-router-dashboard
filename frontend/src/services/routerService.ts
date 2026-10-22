import { MODELS } from "@/lib/routing/models";
import { FALLBACK_RULE, normalizeText, ROUTING_RULES } from "@/lib/routing/rules";
import type { RoutingDecision } from "@/types/chat";

/** Tokens de salida simulados por cada punto de complejidad. */
const OUTPUT_TOKENS_PER_COMPLEXITY = 150;

function estimateComplexity(base: number, prompt: string) {
  const words = prompt.trim().split(/\s+/).length;
  const bonus = words > 120 ? 2 : words > 60 ? 1 : 0;
  return Math.min(10, Math.max(1, base + bonus));
}

/**
 * Router simulado: decide el modelo con reglas por palabras clave.
 * Es síncrono y puro; la latencia se simula en el hook que lo consume.
 */
export function routePrompt(prompt: string): RoutingDecision {
  const text = normalizeText(prompt);

  for (const rule of ROUTING_RULES) {
    const matchedKeywords = rule.keywords.filter((keyword) =>
      text.includes(normalizeText(keyword)),
    );
    if (matchedKeywords.length > 0) {
      return buildDecision(rule.modelId, rule.reason, rule.baseComplexity, prompt, matchedKeywords);
    }
  }

  return buildDecision(
    FALLBACK_RULE.modelId,
    FALLBACK_RULE.reason,
    FALLBACK_RULE.baseComplexity,
    prompt,
    [],
  );
}

function buildDecision(
  modelId: keyof typeof MODELS,
  reason: string,
  baseComplexity: number,
  prompt: string,
  matchedKeywords: string[],
): RoutingDecision {
  const model = MODELS[modelId];
  const complexity = estimateComplexity(baseComplexity, prompt);
  // Aproximación habitual: ~4 caracteres por token.
  const inputTokens = Math.ceil(prompt.length / 4);
  const estimatedTokens = inputTokens + complexity * OUTPUT_TOKENS_PER_COMPLEXITY;
  const estimatedCost = (estimatedTokens / 1000) * model.pricePer1kTokens;

  return {
    model,
    reason,
    matchedKeywords,
    complexity,
    estimatedTokens,
    estimatedCost,
    isFallback: matchedKeywords.length === 0,
  };
}

/** Texto de respuesta simulado que acompaña a la decisión del router. */
export function buildMockReply(decision: RoutingDecision) {
  return `Petición enrutada a ${decision.model.name}. En producción, aquí aparecería la respuesta generada por ${decision.model.provider}.`;
}
