"use client";

import { useState, type FormEvent } from "react";

import { askQuestion } from "@/lib/api/client";
import type { FinalAnswer, SourceHit, Usage } from "@/lib/api/types";
import { vi, type DocType } from "@/lib/i18n/vi";

const types = Object.keys(vi.docTypes) as DocType[];

export function AskDesk() {
  const [question, setQuestion] = useState("");
  const [docType, setDocType] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [hits, setHits] = useState<SourceHit[]>([]);
  const [finalAnswer, setFinalAnswer] = useState<FinalAnswer | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [controller, setController] = useState<AbortController | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const next = new AbortController();
    setController(next);
    setPending(true);
    setError("");
    setFinalAnswer(null);
    setHits([]);
    try {
      const result = await askQuestion(question, docType, next.signal);
      setHits(result.hits);
      setFinalAnswer(result.final);
      setUsage(result.usage);
      const first = result.final.claims.find((claim) => claim.sources[0])?.sources[0]?.chunk_id;
      setSelectedId(first || result.hits[0]?.chunk_id || "");
    } catch (caught) {
      if (caught instanceof Error && caught.name !== "AbortError") {
        setError(caught.message);
      }
    } finally {
      setPending(false);
      setController(null);
    }
  }

  const selected = hits.find((hit) => hit.chunk_id === selectedId) ?? null;

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
      <section className="grid gap-4">
        <header>
          <h1 className="text-2xl font-semibold tracking-tight">{vi.chatTitle}</h1>
          <p className="mt-2 text-sm leading-6 text-stone-600">{vi.chatLead}</p>
        </header>
        <form onSubmit={onSubmit} className="grid gap-3 rounded-lg border border-stone-200 bg-white p-4">
          <label className="grid gap-1 text-sm">
            {vi.docType}
            <select
              className="rounded border border-stone-300 px-2 py-2"
              value={docType}
              onChange={(event) => setDocType(event.target.value)}
            >
              <option value="">{vi.filterAll}</option>
              {types.map((type) => (
                <option key={type} value={type}>
                  {vi.docTypes[type]}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            {vi.question}
            <textarea
              className="min-h-24 rounded border border-stone-300 px-2 py-2"
              value={question}
              required
              onChange={(event) => setQuestion(event.target.value)}
            />
          </label>
          <div className="flex gap-2">
            <button className="rounded bg-stone-900 px-3 py-2 text-sm text-white disabled:opacity-50" type="submit" disabled={pending}>
              {vi.ask}
            </button>
            {pending ? (
              <button className="rounded border border-stone-300 px-3 py-2 text-sm" type="button" onClick={() => controller?.abort()}>
                {vi.stop}
              </button>
            ) : null}
          </div>
        </form>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {!finalAnswer && !pending && !error ? <p className="text-sm text-stone-600">{vi.emptyAnswer}</p> : null}
        {finalAnswer?.insufficient_evidence ? <p className="text-sm text-stone-700">{vi.insufficient}</p> : null}
        {finalAnswer && !finalAnswer.insufficient_evidence ? (
          <article className="grid gap-3">
            <p className="text-base leading-7">{finalAnswer.answer}</p>
            <ul className="grid gap-2">
              {finalAnswer.claims.map((claim) => (
                <li key={claim.text} className="text-sm leading-6">
                  {claim.text}{" "}
                  {claim.status === "unverified" ? <span className="text-red-700">{vi.unverified}</span> : null}
                  {claim.sources.map((source, index) => (
                    <button
                      key={source.chunk_id}
                      type="button"
                      className="ml-1 rounded border border-emerald-700 px-1.5 text-emerald-800"
                      onClick={() => setSelectedId(source.chunk_id)}
                    >
                      {index + 1}
                    </button>
                  ))}
                </li>
              ))}
            </ul>
          </article>
        ) : null}
        {usage ? (
          <p className="text-xs text-stone-500">
            {vi.usage}: {usage.tokens_in} / {usage.tokens_out}. {vi.latency}: {usage.latency_ms} ms.
          </p>
        ) : null}
      </section>
      <aside className="rounded-lg border border-stone-200 bg-white p-4">
        <h2 className="text-sm font-semibold">{vi.sourceTitle}</h2>
        {selected ? (
          <div className="mt-3 grid gap-2 text-sm">
            <p className="font-medium">{selected.document_name}</p>
            <p className="text-stone-600">{selected.section_path.join(" › ")}</p>
            <p className="whitespace-pre-wrap leading-6">{selected.text}</p>
          </div>
        ) : (
          <p className="mt-3 text-sm text-stone-600">{vi.sourceEmpty}</p>
        )}
      </aside>
    </div>
  );
}
