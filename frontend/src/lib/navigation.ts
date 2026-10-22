import type { NavItem } from "@/types";

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "🏠" },
  { label: "Chat Router", href: "/chat", icon: "💬" },
  { label: "Analytics", href: "/analytics", icon: "📊" },
  { label: "Models", href: "/models", icon: "🤖" },
  { label: "Settings", href: "/settings", icon: "⚙️" },
];

export function isActivePath(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}
