"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/types/playground";
import PlaygroundEmptyState from "./PlaygroundEmptyState";
import DecisionEntry from "./DecisionEntry";
import DecisionLoadingIndicator from "./DecisionLoadingIndicator";

interface DecisionHistoryProps {
  messages: Message[];
  isRouting: boolean;
  onSuggestion: (prompt: string) => void;
  onRetry: (errorId: string) => void;
}

export default function DecisionHistory({
  messages,
  isRouting,
  onSuggestion,
  onRetry,
}: DecisionHistoryProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Mantener visible el último mensaje.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, isRouting]);

  if (messages.length === 0 && !isRouting) {
    return (
      <div className="flex-1 overflow-y-auto">
        <PlaygroundEmptyState onSuggestion={onSuggestion} />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto" aria-live="polite">
      <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-6 sm:px-6">
        {messages.map((message) => (
          <DecisionEntry
            key={message.id}
            message={message}
            onRetry={isRouting ? undefined : onRetry}
          />
        ))}
        {isRouting && <DecisionLoadingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
