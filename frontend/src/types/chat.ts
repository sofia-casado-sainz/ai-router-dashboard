/** Modelo elegido por el router; todos los campos vienen del backend. */
export interface AIModel {
  id: string;
  name: string;
  provider: string;
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
