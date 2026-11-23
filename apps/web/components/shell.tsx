import Link from "next/link";
import type { ReactNode } from "react";

import { vi } from "@/lib/i18n/vi";
import { Icon } from "@/components/ui/icon";
import { WorkspaceNav } from "@/components/ui/workspace-nav";

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div>
      <a href="#main-content" className="sr-only skip-link">{vi.skipToContent}</a>
      <header className="topbar">
        <div className="app-width topbar-inner">
          <Link href="/documents" className="brand">
            <span className="brand-mark"><Icon name="brand" size={22} /></span>
            {vi.shellTitle}
          </Link>
          <WorkspaceNav />
        </div>
      </header>
      <main id="main-content" tabIndex={-1} className="app-width app-main">{children}</main>
    </div>
  );
}
