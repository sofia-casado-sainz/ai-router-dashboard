import type { Metadata } from "next";
import MetricsGrid from "@/components/dashboard/MetricsGrid";
import SampleDataBanner from "@/components/dashboard/SampleDataBanner";
import PageHeader from "@/components/layout/PageHeader";
import { getDashboardMetrics } from "@/services/api";

export const metadata: Metadata = { title: "Dashboard" };

export default async function DashboardPage() {
  const metrics = await getDashboardMetrics();

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Consumo, coste y ahorro del enrutado de modelos de IA."
        actions={
          <span className="rounded-lg border border-white/[0.08] bg-zinc-900/60 px-3 py-1.5 text-xs font-medium text-zinc-400">
            {metrics.period} · ejemplo
          </span>
        }
      />
      <SampleDataBanner />
      <MetricsGrid metrics={metrics} />
    </>
  );
}
