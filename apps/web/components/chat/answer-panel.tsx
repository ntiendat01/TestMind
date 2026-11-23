import Link from "next/link";

import { Icon } from "@/components/ui/icon";
import type { askQuestion } from "@/lib/api/client";
import type { Evidence } from "@/lib/api/citations";
import { vi } from "@/lib/i18n/vi";
import styles from "./chat.module.css";

type Ready = {
  kind: "ready";
  query: string;
  result: Awaited<ReturnType<typeof askQuestion>>;
  sources: Evidence[];
};

export type AnswerState =
  | { kind: "idle" | "pending" | "cancelled" }
  | { kind: "error"; message: string }
  | Ready;

type CitationHandler = (sourceId: string, trigger: HTMLButtonElement) => void;

export function AnswerPanel({ state, selectedId, onCitation }: {
  state: AnswerState; selectedId: string; onCitation: CitationHandler;
}) {
  return (
    <section className={`panel ${styles.answer}`} aria-labelledby="answer-title" aria-busy={state.kind === "pending"}>
      <div className={styles.panelHead}>
        <span className={styles.panelIcon}><Icon name="chat" size={19} /></span>
        <h2 id="answer-title" className="panel-title">{vi.answerTitle}</h2>
      </div>
      <div className={styles.answerBody}>
        <div className="sr-only" role="status">
          {state.kind === "ready" ? vi.answerTitle : state.kind === "pending" ? vi.loadingAnswer : ""}
        </div>
        {state.kind === "idle" && (
          <div className={styles.emptyAnswer}>
            <strong>{vi.answerEmptyTitle}</strong>
            <p>{vi.emptyAnswer}</p>
            <Link className="text-link" href="/documents">{vi.upload}</Link>
          </div>
        )}
        {state.kind === "pending" && <p className="feedback">{vi.loadingAnswer}</p>}
        {state.kind === "cancelled" && <p className="feedback" role="status">{vi.cancelledAnswer}</p>}
        {state.kind === "error" && <p className="feedback" data-tone="error" role="alert">{state.message}</p>}
        {state.kind === "ready" && <AnswerResult state={state} selectedId={selectedId} onCitation={onCitation} />}
      </div>
    </section>
  );
}

function AnswerResult({ state, selectedId, onCitation }: {
  state: Ready; selectedId: string; onCitation: CitationHandler;
}) {
  const { final, usage } = state.result;
  const lookup = new Map(state.sources.map((item) => [item.hit.chunk_id, item]));
  const hasSeparateSummary = final.claims.length !== 1
    || final.claims[0].text.trim() !== final.answer.trim();

  return (
    <div className={styles.result}>
      <p className={styles.askedQuestion}>{state.query}</p>
      {final.insufficient_evidence ? (
        <div className="feedback" data-tone="warning">
          <strong>{vi.insufficientTitle}</strong>
          <p>{state.sources.length ? vi.insufficient : vi.noSourceFound}</p>
        </div>
      ) : (
        <>
          {hasSeparateSummary && final.answer && <p className={styles.summary}>{final.answer}</p>}
          {final.claims.length === 0 && <p className="feedback" data-tone="warning">{vi.unverified}</p>}
          {final.claims.length > 0 && (
            <ul className={styles.claims}>
              {final.claims.map((claim, index) => {
                const cited = [...new Set(claim.sources.map((source) => source.chunk_id))]
                  .flatMap((id) => lookup.get(id) ?? []);
                return (
                  <li key={index}>
                    <p className="wrap">{claim.text}</p>
                    <div className={styles.citations}>
                      {cited.map(({ hit, label }) => (
                        <button
                          key={hit.chunk_id} type="button" className={styles.citation}
                          aria-controls="source-panel" aria-pressed={selectedId === hit.chunk_id}
                          aria-label={vi.sourceOpen(label, hit.document_name)}
                          onClick={(event) => onCitation(hit.chunk_id, event.currentTarget)}>
                          {label} <Icon name="external" size={14} />
                        </button>
                      ))}
                      {(claim.status === "unverified" || !cited.length) && (
                        <span className={styles.warning}>{vi.unverified}</span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
      <details className={styles.usage}>
        <summary>{vi.usageTitle}</summary>
        <dl>
          <div><dt>{vi.usage}</dt><dd>{usage.tokens_in} / {usage.tokens_out}</dd></div>
          <div><dt>{vi.latency}</dt><dd>{usage.latency_ms} ms</dd></div>
        </dl>
      </details>
    </div>
  );
}
