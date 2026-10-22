"use client";

import { useState } from "react";

export default function ChatPanel() {
  const [prompt, setPrompt] = useState("");

  const sendPrompt = async () => {
    console.log(prompt);
  };

  return (
    <div className="bg-zinc-900 p-6 rounded-xl">

      <h2 className="text-xl font-bold mb-4">
        Chat Router
      </h2>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        className="w-full h-40 bg-zinc-800 p-4 rounded"
        placeholder="Describe lo que necesitas..."
      />

      <button
        onClick={sendPrompt}
        className="mt-4 bg-blue-600 px-4 py-2 rounded"
      >
        Enviar
      </button>

    </div>
  );
}