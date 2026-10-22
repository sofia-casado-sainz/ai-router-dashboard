import type { Metadata } from "next";
import ComingSoon from "@/components/layout/ComingSoon";
import PageHeader from "@/components/layout/PageHeader";

export const metadata: Metadata = { title: "Analytics" };

export default function AnalyticsPage() {
  return (
    <>
      <PageHeader
        title="Analytics"
        description="Evolución de uso, costes y latencia por modelo."
      />
      <ComingSoon icon="📊" message="Aquí verás gráficas de consumo y coste por modelo." />
    </>
  );
}
