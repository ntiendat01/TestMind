import Link from "next/link";
import type { ReactNode } from "react";

import { vi } from "@/lib/i18n/vi";

export function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link href="/documents" className="text-sm font-semibold tracking-tight">
            {vi.shellTitle}
          </Link>
          <nav className="flex gap-4 text-sm">
            <Link href="/documents" className="text-stone-700 hover:text-stone-950">
              {vi.navDocuments}
            </Link>
            <Link href="/chat" className="text-stone-700 hover:text-stone-950">
              {vi.navChat}
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}
