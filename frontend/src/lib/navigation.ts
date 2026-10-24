import type { NavItem } from "@/types";

/** Funcionalidades implementadas. */
export const NAV_ITEMS: NavItem[] = [
  { label: "Playground", href: "/playground", icon: "🧭" },
  { label: "Dashboard", href: "/dashboard", icon: "🏠" },
  { label: "Models", href: "/models", icon: "🤖" },
];

/** Funcionalidades previstas: cada una indica el sprint en el que llegará. */
export const UPCOMING_NAV_ITEMS: NavItem[] = [
  { label: "Analytics", href: "/analytics", icon: "📊", sprint: "S6" },
  { label: "Settings", href: "/settings", icon: "⚙️", sprint: "Futuro" },
];

export function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}
