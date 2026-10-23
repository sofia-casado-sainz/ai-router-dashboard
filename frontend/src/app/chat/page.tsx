import { redirect } from "next/navigation";

/**
 * Ruta anterior del Playground; se mantiene para no romper enlaces existentes.
 * Redirección temporal (307): una permanente quedaría en la caché del navegador
 * e impediría reutilizar /chat en sprints futuros.
 */
export default function LegacyChatRedirect() {
  redirect("/playground");
}
