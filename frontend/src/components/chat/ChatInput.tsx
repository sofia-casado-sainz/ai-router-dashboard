"use client";

import { useRef, useState, type FormEvent, type KeyboardEvent } from "react";

const MAX_HEIGHT = 200;

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const canSend = value.trim().length > 0 && !disabled;

  const resize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
  };

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    if (!canSend) return;
    onSend(value);
    setValue("");
    requestAnimationFrame(resize);
  };

  // Enter envía; Shift+Enter inserta salto de línea.
  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <form onSubmit={submit} className="border-t border-white/[0.06] bg-zinc-950/80 p-3 sm:p-4">
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-white/[0.08] bg-zinc-900 p-2 transition-colors focus-within:border-indigo-500/50 focus-within:ring-2 focus-within:ring-indigo-500/20">
        <label htmlFor="chat-prompt" className="sr-only">
          Prompt
        </label>
        <textarea
          id="chat-prompt"
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            resize();
          }}
          onKeyDown={onKeyDown}
          placeholder="Describe lo que necesitas..."
          className="max-h-[200px] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none"
        />
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Enviar"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-500 text-white transition-colors hover:bg-indigo-400 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500"
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
            <path d="M3.105 2.288a.75.75 0 0 0-.826.95l1.414 4.926A1.5 1.5 0 0 0 5.135 9.25h6.115a.75.75 0 0 1 0 1.5H5.135a1.5 1.5 0 0 0-1.442 1.086l-1.414 4.926a.75.75 0 0 0 .826.95 28.897 28.897 0 0 0 15.293-7.155.75.75 0 0 0 0-1.114A28.897 28.897 0 0 0 3.105 2.288Z" />
          </svg>
        </button>
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-zinc-600">
        Modo simulación · Las respuestas y costes son datos mock.
      </p>
    </form>
  );
}
