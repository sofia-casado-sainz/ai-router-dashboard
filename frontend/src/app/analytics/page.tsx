import type { Metadata } from "next";
import PageHeader from "@/components/layout/PageHeader";
import PlannedFeature from "@/components/layout/PlannedFeature";

export const metadata: Metadata = { title: "Analytics" };

export default function AnalyticsPage() {
  return (
    <>
      <PageHeader
        title="Analytics"
        description="Evolución de uso, costes y latencia por modelo."
      />
      <PlannedFeature
        icon="📊"
        availability="Sprint S6"
        goal="Analytics llegará en el Sprint S6."
        description="Mostrará cómo evolucionan el uso y el coste a partir de peticiones reales. Antes necesita la persistencia (S1) y la ejecución real de los modelos (S2), para medir en lugar de estimar."
        capabilities={[
          "Coste real frente a una línea base declarada",
          "Reparto de peticiones por modelo y tipo de tarea",
          "Distribución de la complejidad de las tareas",
          "Tasa de decisiones sin regla específica",
        ]}
      />
    </>
  );
}
