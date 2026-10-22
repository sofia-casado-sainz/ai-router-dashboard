"use client";

import type { ReactNode } from "react";
import { useDisclosure } from "@/hooks/useDisclosure";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

/** Layout reutilizable: sidebar fija en desktop y drawer en móvil. */
export default function AppShell({ children }: { children: ReactNode }) {
  const sidebar = useDisclosure();

  return (
    <div className="min-h-screen">
      <Sidebar open={sidebar.isOpen} onClose={sidebar.close} />

      <div className="flex min-h-screen flex-col lg:pl-64">
        <Topbar onMenuClick={sidebar.open} menuOpen={sidebar.isOpen} />
        <main className="flex-1 px-4 py-8 sm:px-6 lg:px-10 lg:py-10">
          <div className="mx-auto w-full max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
