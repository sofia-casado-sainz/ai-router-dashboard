"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, routePrompt } from "@/services/routerApi";
import type { Message, RoutingDecision } from "@/types/chat";

function createId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function buildReply(decision: RoutingDecision) {
  return `Petición enrutada a ${decision.model.name}. La generación de la respuesta se conectará en la siguiente fase.`;
}

/** Estado del chat: mensajes, envío al backend y gestión de errores. */
export function useChatRouter() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRouting, setIsRouting] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  // Cancelar la petición en curso si se abandona la página.
  useEffect(() => () => abortRef.current?.abort(), []);

  const requestRoute = useCallback(async (prompt: string) => {
    const controller = new AbortController();
    abortRef.current = controller;
    setIsRouting(true);

    try {
      const decision = await routePrompt(prompt, controller.signal);
      setMessages((prev) => [
        ...prev,
        {
          id: createId(),
          role: "router",
          decision,
          content: buildReply(decision),
          createdAt: new Date(),
        },
      ]);
    } catch (error) {
      if (controller.signal.aborted) return;
      setMessages((prev) => [
        ...prev,
        {
          id: createId(),
          role: "error",
          prompt,
          content: error instanceof ApiError ? error.message : "Error inesperado al enrutar.",
          createdAt: new Date(),
        },
      ]);
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
        setIsRouting(false);
      }
    }
  }, []);

  const sendMessage = useCallback(
    (rawContent: string) => {
      const content = rawContent.trim();
      if (!content || isRouting) return;

      setMessages((prev) => [
        ...prev,
        { id: createId(), role: "user", content, createdAt: new Date() },
      ]);
      void requestRoute(content);
    },
    [isRouting, requestRoute],
  );

  const retry = useCallback(
    (errorId: string) => {
      const failed = messages.find((m) => m.id === errorId);
      if (!failed || failed.role !== "error" || isRouting) return;

      setMessages((prev) => prev.filter((m) => m.id !== errorId));
      void requestRoute(failed.prompt);
    },
    [messages, isRouting, requestRoute],
  );

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setMessages([]);
    setIsRouting(false);
  }, []);

  return { messages, isRouting, sendMessage, retry, reset };
}
