"use client";

import { useCallback, useState } from "react";

/** Estado abierto/cerrado reutilizable para drawers, modales y menús. */
export function useDisclosure(initial = false) {
  const [isOpen, setIsOpen] = useState(initial);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);

  return { isOpen, open, close };
}
