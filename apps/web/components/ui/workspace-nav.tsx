"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { vi } from "@/lib/i18n/vi";
import { Icon } from "./icon";

const destinations = [
  { href: "/documents", label: vi.navDocuments, icon: "document" },
  { href: "/chat", label: vi.navChat, icon: "chat" },
] as const;

export function WorkspaceNav() {
  const pathname = usePathname();
  return (
    <nav className="topnav" aria-label={vi.workspaceNavigation}>
      {destinations.map(({ href, label, icon }) => (
        <Link key={href} href={href} className="nav-link"
          aria-current={pathname === href ? "page" : undefined}>
          <Icon name={icon} size={18} /> {label}
        </Link>
      ))}
    </nav>
  );
}
