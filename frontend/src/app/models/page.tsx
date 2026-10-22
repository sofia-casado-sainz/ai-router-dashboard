import type { Metadata } from "next";
import ComingSoon from "@/components/layout/ComingSoon";
import PageHeader from "@/components/layout/PageHeader";

export const metadata: Metadata = { title: "Models" };

export default function ModelsPage() {
  return (
    <>
      <PageHeader
        title="Models"
        description="Catálogo de modelos disponibles para el enrutado."
      />
      <ComingSoon icon="🤖" message="Aquí podrás activar, priorizar y comparar modelos." />
    </>
  );
}
