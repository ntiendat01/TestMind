import type { Metadata } from "next";
import type { ReactNode } from "react";

import { vi } from "@/lib/i18n/vi";

import "./globals.css";

export const metadata: Metadata = {
  title: vi.shellTitle,
  description: vi.documentsLead,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi">
      <body className="antialiased">{children}</body>
    </html>
  );
}
