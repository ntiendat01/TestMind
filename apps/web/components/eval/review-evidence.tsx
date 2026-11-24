import { useRef, useState } from "react";

import { stringList, textValue, type ReviewCase } from "@/lib/api/review";
import { vi } from "@/lib/i18n/vi";
import styles from "./review.module.css";

function location(source: Record<string, unknown>): string {
  const parts = stringList(source.section_path);
  const loc = source.loc;
  if (loc && typeof loc === "object") {
    if ("sheet" in loc && typeof loc.sheet === "string") parts.push(vi.sourceSheet(loc.sheet));
    if ("row" in loc && typeof loc.row === "number") parts.push(vi.sourceRow(loc.row));
    if ("page" in loc && typeof loc.page === "number") parts.push(vi.sourcePage(loc.page));
    if ("paragraph_idx" in loc && typeof loc.paragraph_idx === "number") parts.push(vi.sourceBlock(loc.paragraph_idx));
  }
  return parts.join(" · ");
}

export function ReviewEvidence({ item }: { item: ReviewCase }) {
  const t = vi.review;
  const observation = item.observation;
  const lastCitation = useRef<HTMLButtonElement | null>(null);
  const [canReturn, setCanReturn] = useState(false);
  const sourceRefs = useRef<(HTMLDetailsElement | null)[]>([]);
  function openSource(index: number, trigger: HTMLButtonElement) {
    const source = sourceRefs.current[index];
    if (!source) return;
    lastCitation.current = trigger;
    setCanReturn(true);
    source.open = true;
    source.focus({ preventScroll: true });
    source.scrollIntoView({ block: "nearest" });
  }
  return (
    <div className={styles.evidenceColumn}>
      <section className={`panel ${styles.answerPanel}`} aria-labelledby="review-question">
        <div className={styles.caseMeta}>
          <span className="mono">{item.split} / {observation.id}</span>
          <span>{observation.context === "gold" ? t.gold : t.retrieved}</span>
        </div>
        <span className={styles.eyebrow}>{t.question}</span>
        <h2 className={styles.question} id="review-question">{observation.question}</h2>
        <div className={styles.answerHead}>
          <h3>{t.answer}</h3>
          <span className={styles.badge}>{observation.refused === true ? t.refused : observation.refused === false ? t.answered : t.unknownOutcome}</span>
        </div>
        {observation.error && <p className="feedback" data-tone="warning">{t.generationError}</p>}
        <p className={styles.answerText}>{observation.answer || t.noAnswer}</p>
        {observation.notes && <p className={`muted ${styles.answerText}`}>{observation.notes}</p>}
        {!!observation.claims?.length && <div className={styles.claims}>
          <h3>{t.claims}</h3>
          <ul>{observation.claims.map((claim, i) => <li key={i}>
            <p className="wrap">{textValue(claim.text)}</p>
            <div className={styles.citations}>{stringList(claim.chunk_ids).map(id => {
              const index = observation.sources.findIndex(source => source.chunk_id === id);
              return index < 0 ? <span key={id} className="muted">{t.sourceMissing}</span> : (
                <button key={id} className={styles.citation} onClick={event => openSource(index, event.currentTarget)}>
                  {t.source(index + 1)}
                </button>
              );
            })}{!stringList(claim.chunk_ids).length && <span className="muted">{t.noCitation}</span>}</div>
          </li>)}</ul>
        </div>}
        <div className={styles.expected}>
          <h3>{t.expected}</h3>
          <p className="muted">{observation.answerable ? t.expectedAnswerable : t.expectedRefusal}</p>
          <ul>{observation.expected_points.map((point, i) => <li key={i}>{point}</li>)}</ul>
        </div>
        <a className={`button secondary ${styles.mobileScore}`} href="#score-title">{t.goToScore}</a>
        <details className={styles.provenance}>
          <summary>{t.provenance}</summary>
          <p className="mono wrap">{item.source_run_id}</p>
          {item.recovered && <p>{t.recovered}</p>}
          <p className="mono wrap">SHA-256 · {item.observation_sha256}</p>
        </details>
      </section>
      <section className={`panel ${styles.sourcesPanel}`} aria-labelledby="review-sources">
        <h2 id="review-sources" className="panel-title">{t.sources} <span className={`mono ${styles.sourceCount}`}>{observation.sources.length}</span></h2>
        {!observation.sources.length && <p className="muted">{t.noSources}</p>}
        {observation.sources.map((source, index) => <details key={index} className={styles.source}
          ref={element => { sourceRefs.current[index] = element; }} tabIndex={-1}>
          <summary><span className={styles.sourceNumber}>{String(index + 1).padStart(2, "0")}</span>
            <span className="wrap">{textValue(source.document)}<small>{location(source)}</small></span>
          </summary>
          {canReturn && <button className="text-link" onClick={() => lastCitation.current?.focus()}>{vi.sourceBack}</button>}
          <blockquote className="wrap">{textValue(source.text)}</blockquote>
        </details>)}
      </section>
    </div>
  );
}
