import type { Metadata } from "next";
import ComingSoon from "@/components/layout/ComingSoon";
import PageHeader from "@/components/layout/PageHeader";

export const metadata: Metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        title="Settings"
        description="Configuración del workspace, claves de API y preferencias."
      />
      <ComingSoon icon="⚙️" message="Aquí gestionarás proveedores, presupuestos y reglas de enrutado." />
    </>
  );
}
