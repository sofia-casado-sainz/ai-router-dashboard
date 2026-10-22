import { formatTime } from "@/lib/format";
import type { Message } from "@/types/chat";
import ModelSelectionCard from "./ModelSelectionCard";

export default function ChatMessage({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] sm:max-w-[75%]">
          <div className="whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-indigo-500 px-4 py-2.5 text-sm text-white">
            {message.content}
          </div>
          <p className="mt-1 text-right text-[11px] text-zinc-600">
            {formatTime(message.createdAt)}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <RouterAvatar />
      <div className="min-w-0 max-w-[85%] flex-1 sm:max-w-[75%]">
        <p className="mb-2 text-xs font-medium text-zinc-400">
          AI Router <span className="text-zinc-600">· {formatTime(message.createdAt)}</span>
        </p>
        <ModelSelectionCard decision={message.decision} />
        <p className="mt-3 text-sm text-zinc-400">{message.content}</p>
      </div>
    </div>
  );
}

export function RouterAvatar() {
  return (
    <span
      aria-hidden
      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-linear-to-br from-indigo-500 to-violet-600 text-[11px] font-bold text-white"
    >
      AR
    </span>
  );
}
