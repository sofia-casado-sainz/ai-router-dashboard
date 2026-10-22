import ChatPanel from "./ChatPanel";
import StatsCards from "./StatsCards";

export default function Dashboard() {
  return (
    <main className="min-h-screen bg-zinc-950 text-white p-8">
      <h1 className="text-4xl font-bold mb-8">
        🤖 AI Router Dashboard
      </h1>

      <StatsCards />

      <div className="mt-8">
        <ChatPanel />
      </div>
    </main>
  );
}