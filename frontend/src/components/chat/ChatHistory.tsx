"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/types/chat";
import ChatEmptyState from "./ChatEmptyState";
import ChatMessage from "./ChatMessage";
import TypingIndicator from "./TypingIndicator";

interface ChatHistoryProps {
  messages: Message[];
  isRouting: boolean;
  onSuggestion: (prompt: string) => void;
}

export default function ChatHistory({ messages, isRouting, onSuggestion }: ChatHistoryProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Mantener visible el último mensaje.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, isRouting]);

  if (messages.length === 0 && !isRouting) {
    return (
      <div className="flex-1 overflow-y-auto">
        <ChatEmptyState onSuggestion={onSuggestion} />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto" aria-live="polite">
      <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-6 sm:px-6">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isRouting && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
