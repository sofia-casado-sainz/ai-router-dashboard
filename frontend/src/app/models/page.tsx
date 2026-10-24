import type { Metadata } from "next";
import PageHeader from "@/components/layout/PageHeader";
import ModelCatalog from "@/components/models/ModelCatalog";

export const metadata: Metadata = { title: "Models" };

export default function ModelsPage() {
  return (
    <>
      <PageHeader
        title="Models"
        description="Catálogo persistente de modelos: proveedor, ventana de contexto, precio vigente y si están activos para el enrutado."
      />
      <ModelCatalog />
    </>
  );
}
