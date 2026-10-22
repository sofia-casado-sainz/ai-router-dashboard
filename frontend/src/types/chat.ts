export type ModelId = "claude-sonnet" | "gemini" | "gpt" | "deepseek";

export interface AIModel {
  id: ModelId;
  name: string;
  provider: string;
  /** Precio simulado en € por cada 1.000 tokens. */
  pricePer1kTokens: number;
  tagline: string;
}

export interface RoutingRule {
  id: string;
  modelId: ModelId;
  keywords: string[];
  reason: string;
  /** Complejidad base (1-10) asociada a este tipo de tarea. */
  baseComplexity: number;
}

export interface RoutingDecision {
  model: AIModel;
  reason: string;
  /** Palabras clave del prompt que activaron la regla (vacío si es fallback). */
  matchedKeywords: string[];
  complexity: number;
  estimatedTokens: number;
  estimatedCost: number;
  isFallback: boolean;
}

interface BaseMessage {
  id: string;
  createdAt: Date;
}

export interface UserMessage extends BaseMessage {
  role: "user";
  content: string;
}

export interface RouterMessage extends BaseMessage {
  role: "router";
  decision: RoutingDecision;
  content: string;
}

export interface ErrorMessage extends BaseMessage {
  role: "error";
  content: string;
  /** Prompt que falló, para poder reintentarlo. */
  prompt: string;
}

export type Message = UserMessage | RouterMessage | ErrorMessage;
