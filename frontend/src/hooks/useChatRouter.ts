"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { buildMockReply, routePrompt } from "@/services/routerService";
import type { Message } from "@/types/chat";

/** Latencia simulada del router (ms). */
const MIN_LATENCY = 600;
const MAX_LATENCY = 1200;

function createId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Estado del chat: mensajes, envío y respuesta simulada del router. */
export function useChatRouter() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRouting, setIsRouting] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const sendMessage = useCallback(
    (rawContent: string) => {
      const content = rawContent.trim();
      if (!content || isRouting) return;

      setMessages((prev) => [
        ...prev,
        { id: createId(), role: "user", content, createdAt: new Date() },
      ]);
      setIsRouting(true);

      const latency = MIN_LATENCY + Math.random() * (MAX_LATENCY - MIN_LATENCY);
      timeoutRef.current = setTimeout(() => {
        const decision = routePrompt(content);
        setMessages((prev) => [
          ...prev,
          {
            id: createId(),
            role: "router",
            decision,
            content: buildMockReply(decision),
            createdAt: new Date(),
          },
        ]);
        setIsRouting(false);
      }, latency);
    },
    [isRouting],
  );

  const reset = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setMessages([]);
    setIsRouting(false);
  }, []);

  return { messages, isRouting, sendMessage, reset };
}
