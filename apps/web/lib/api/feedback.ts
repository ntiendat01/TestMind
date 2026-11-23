import { vi } from "@/lib/i18n/vi";
import { ApiError } from "./client";

export function requestFeedback(error: unknown, fallback: string): string {
  if (!(error instanceof ApiError)) return fallback;
  const code = error.status === 429 ? "rate_limited" : error.code;
  return Object.hasOwn(vi.apiErrors, code) ? vi.apiErrors[code as keyof typeof vi.apiErrors] : fallback;
}
