import { permanentRedirect } from "next/navigation";

/** Ruta anterior del Playground; se mantiene para no romper enlaces existentes. */
export default function LegacyChatRedirect() {
  permanentRedirect("/playground");
}
