"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { isActivePath } from "@/lib/navigation";
import { cn } from "@/lib/utils";
import type { NavItem } from "@/types";

interface SidebarNavLinkProps {
  item: NavItem;
  onNavigate?: () => void;
}

export default function SidebarNavLink({ item, onNavigate }: SidebarNavLinkProps) {
  const pathname = usePathname();
  const active = isActivePath(pathname, item.href);

  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
        active
          ? "bg-white/[0.08] text-white"
          : "text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100",
      )}
    >
      <span aria-hidden className="text-base leading-none">
        {item.icon}
      </span>
      <span>{item.label}</span>
      {active && (
        <span aria-hidden className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-400" />
      )}
    </Link>
  );
}
