"use client";

import { useEffect } from "react";
import { NAV_ITEMS, UPCOMING_NAV_ITEMS } from "@/lib/navigation";
import { cn } from "@/lib/utils";
import Logo from "./Logo";
import SidebarNavLink from "./SidebarNavLink";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  // En móvil: cerrar con Escape y bloquear el scroll del fondo mientras está abierta.
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  return (
    <>
      {/* Overlay (solo móvil) */}
      <div
        aria-hidden
        onClick={onClose}
        className={cn(
          "fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity lg:hidden",
          open ? "opacity-100" : "pointer-events-none opacity-0",
        )}
      />

      <aside
        id="app-sidebar"
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-white/[0.06] bg-zinc-950 transition-transform duration-200 ease-out",
          "lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center justify-between px-5">
          <Logo />
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar menú"
            className="rounded-md p-1.5 text-zinc-400 hover:bg-white/[0.06] hover:text-white lg:hidden"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <p className="px-3 pb-2 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Plataforma
          </p>
          <ul className="space-y-1">
            {NAV_ITEMS.map((item) => (
              <li key={item.href}>
                <SidebarNavLink item={item} onNavigate={onClose} />
              </li>
            ))}
          </ul>

          <p className="mt-6 px-3 pb-2 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Próximamente
          </p>
          <ul className="space-y-1">
            {UPCOMING_NAV_ITEMS.map((item) => (
              <li key={item.href}>
                <SidebarNavLink item={item} onNavigate={onClose} />
              </li>
            ))}
          </ul>
        </nav>

        <div className="border-t border-white/[0.06] p-4">
          <div className="flex items-center gap-3 rounded-lg px-2 py-1.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-800 font-mono text-xs font-medium text-zinc-300">
              v0
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-zinc-200">Proyecto demo</p>
              <p className="truncate text-xs text-zinc-500">Router v0 · datos simulados</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
