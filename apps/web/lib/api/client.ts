import { readSse } from "@/lib/sse/parse";

import type { ApiErrorBody, DocumentRow, FinalAnswer, JobRow, SourceHit, Usage } from "./types";

const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public readonly code: string, public readonly status: number) {
    super(code);
  }
}

export function apiBase(): string {
  return base;
}

export async function listDocuments(): Promise<DocumentRow[]> {
  return readJson(await fetch(`${base}/v1/documents`));
}

export async function uploadDocument(file: File, docType: string, module: string): Promise<{ job_id: string }> {
  const body = new FormData();
  body.set("file", file);
  body.set("doc_type", docType);
  if (module.trim()) {
    body.set("module", module.trim());
  }
  return readJson(await fetch(`${base}/v1/documents`, { method: "POST", body }));
}

export async function readJob(jobId: string): Promise<JobRow> {
  return readJson(await fetch(`${base}/v1/jobs/${jobId}`));
}

export async function askQuestion(
  query: string,
  filters: { docType: string; module: string },
  signal: AbortSignal,
): Promise<{ hits: SourceHit[]; final: FinalAnswer; usage: Usage }> {
  const response = await fetch(`${base}/v1/query`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      query,
      doc_types: filters.docType ? [filters.docType] : [],
      module: filters.module.trim() || null,
    }),
    signal,
  });
  if (!response.ok) {
    throw await toError(response);
  }
  const hits: SourceHit[] = [];
  let final: FinalAnswer | null = null;
  let usage: Usage | null = null;
  for await (const event of readSse(response)) {
    if (event.event === "retrieval") {
      hits.push(...(JSON.parse(event.data) as SourceHit[]));
    } else if (event.event === "final") {
      final = JSON.parse(event.data) as FinalAnswer;
    } else if (event.event === "usage") {
      usage = JSON.parse(event.data) as Usage;
    }
  }
  if (!final || !usage) {
    throw new Error("incomplete");
  }
  return { hits, final, usage };
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw await toError(response);
  }
  return (await response.json()) as T;
}

async function toError(response: Response): Promise<Error> {
  try {
    const body = (await response.json()) as ApiErrorBody;
    return new ApiError(body?.code || "request_failed", response.status);
  } catch {
    return new ApiError("request_failed", response.status);
  }
}
