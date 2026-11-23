import { afterEach, describe, expect, it, vi } from "vitest";

import { askQuestion, listDocuments } from "./client";
import { requestFeedback } from "./feedback";

afterEach(() => vi.unstubAllGlobals());

describe("query client", () => {
  it("sends both filters and reads final SSE data", async () => {
    const usage = { tokens_in: 12, tokens_out: 5, latency_ms: 300, prompt_version: "v1" };
    const final = { insufficient_evidence: true, answer: "", claims: [], notes: "" };
    const fetch = vi.fn<typeof globalThis.fetch>().mockResolvedValue(new Response(
      `event: retrieval\ndata: []\n\nevent: final\ndata: ${JSON.stringify(final)}\n\n`
      + `event: usage\ndata: ${JSON.stringify(usage)}\n\n`,
    ));
    vi.stubGlobal("fetch", fetch);
    const signal = new AbortController().signal;
    await expect(askQuestion("Điều kiện?", { docType: "brd", module: " refund " }, signal))
      .resolves.toEqual({ hits: [], final, usage });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/v1/query"), expect.objectContaining({
      signal,
      body: JSON.stringify({ query: "Điều kiện?", doc_types: ["brd"], module: "refund" }),
    }));
  });

  it("uses friendly rate-limit feedback even if the server sends HTML", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("rate limited", { status: 429 })));
    await expect(listDocuments()).rejects.toMatchObject({ status: 429 });
    const message = await listDocuments().catch((error: unknown) => requestFeedback(error, "fallback"));
    expect(message).toContain("Chờ một lát");
  });
});
