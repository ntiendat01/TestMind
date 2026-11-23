import { vi } from "@/lib/i18n/vi";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-6">
      <p className="text-sm text-neutral-500">{vi.shellEyebrow}</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight">{vi.shellTitle}</h1>
      <p className="mt-4 text-base leading-7 text-neutral-700">{vi.shellBody}</p>
    </main>
  );
}
