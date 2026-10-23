import type { Metadata } from "next";
import PageHeader from "@/components/layout/PageHeader";
import PlannedFeature from "@/components/layout/PlannedFeature";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        title="Settings"
        description="Proveedores, presupuestos y reglas de enrutado."
      />
      <PlannedFeature
        icon="⚙️"
        availability="Fase futura"
        goal="Settings llegará en una fase posterior."
        description="Reunirá la configuración que hoy no existe porque el producto todavía no tiene usuarios ni equipos. Cada bloque llegará con el sprint que lo hace necesario."
        capabilities={[
          "Conexión con proveedores (OpenRouter, Ollama) · S2–S3",
          "Equipos y claves de API · S4",
          "Reglas de enrutado configurables · S5",
          "Presupuestos y alertas · S6",
        ]}
      />
    </>
  );
}
