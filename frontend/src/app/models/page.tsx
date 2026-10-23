import type { Metadata } from "next";
import PageHeader from "@/components/layout/PageHeader";
import PlannedFeature from "@/components/layout/PlannedFeature";

export const metadata: Metadata = { title: "Models" };

export default function ModelsPage() {
  return (
    <>
      <PageHeader
        title="Models"
        description="Catálogo de modelos disponibles para el enrutado."
      />
      <PlannedFeature
        icon="🤖"
        availability="Sprint S1"
        goal="Models llegará en el Sprint S1."
        description="Permitirá consultar modelos, proveedores, precios y ventana de contexto desde un catálogo persistente en PostgreSQL. Hoy el catálogo vive en el código del backend y el router lo consulta directamente."
        capabilities={[
          "Catálogo de modelos y proveedores",
          "Precio de entrada y de salida por millón de tokens",
          "Ventana de contexto de cada modelo",
          "Estado activo o inactivo para el enrutado",
        ]}
      />
    </>
  );
}
