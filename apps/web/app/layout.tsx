import type { Metadata } from "next";
import localFont from "next/font/local";
import type { ReactNode } from "react";

import { vi } from "@/lib/i18n/vi";

import "./globals.css";

const manrope = localFont({
  src: "../public/manrope.ttf",
  weight: "200 800",
  display: "swap",
  variable: "--font-manrope",
});

export const metadata: Metadata = {
  title: vi.shellTitle,
  description: vi.documentsLead,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" className={manrope.variable}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
