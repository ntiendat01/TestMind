"use client";

import { useEffect, useRef, useState } from "react";

import { Icon } from "@/components/ui/icon";
import { useReview } from "@/hooks/use-review";
import { emptyScore, isComplete } from "@/lib/api/review";
import { vi } from "@/lib/i18n/vi";
import { ReviewEvidence } from "./review-evidence";
import { ReviewNavigation } from "./review-navigation";
import { ReviewScoreForm } from "./review-score-form";
import { ReviewToolbar } from "./review-toolbar";
import styles from "./review.module.css";

export function ReviewDesk() {
  const review = useReview();
  const [context, setContext] = useState("all");
  const feedback = useRef<HTMLDivElement>(null);
  const t = vi.review;
  const filtered = review.cases.filter(item => context === "all" || item.observation.context === context);
  const selected = filtered.find(item => item.case_id === review.selectedId) ?? filtered[0];
  const complete = review.cases.filter(item => isComplete(item, review.ratings[item.case_id])).length;
  const hasErrors = !!review.error || review.needsReasons.length > 0;
  useEffect(() => { if (hasErrors) feedback.current?.focus(); }, [hasErrors, review.error, review.needsReasons]);
  function selectCase(id: string) {
    review.setSelectedId(id);
  }
  return (
    <div className={styles.desk}>
      <header className={styles.header}>
        <div><p className={styles.eyebrow}>{t.eyebrow}</p><h1>{t.title}</h1><p className="muted">{t.lead}</p></div>
        <ReviewToolbar hasPacket={!!review.cases.length} busy={review.busy} canExport={!!review.reviewer.trim()}
          onImport={review.importFile} onExport={review.exportScores} />
      </header>
      <div ref={feedback} tabIndex={-1} className={styles.feedbackRegion}>
        {review.busy && <p className="feedback" role="status">{t.busy}</p>}
        {review.error && <p className="feedback" data-tone="error" role="alert">{review.error}</p>}
        {!!review.needsReasons.length && <div className="feedback" data-tone="error" role="alert">
          <p>{t.reasonsNeeded}</p><div className={styles.reasonLinks}>{review.needsReasons.map(id => (
            <button key={id} className="text-link" onClick={() => {
              setContext("all"); selectCase(id);
              requestAnimationFrame(() => document.getElementById("review-comments")?.focus());
            }}>{id}</button>
          ))}</div>
        </div>}
        {review.notice && <p className="feedback" data-tone="success" role="status">{review.notice}</p>}
      </div>
      {review.cases.length ? <>
        <section className={`panel ${styles.session}`} aria-label={t.reviewer}>
          <label className="field">{t.reviewer}
            <input className="control" value={review.reviewer} placeholder={t.reviewerPlaceholder} maxLength={120}
              disabled={review.busy || review.identityLocked} aria-describedby="review-identity-hint"
              onChange={event => review.changeReviewer(event.target.value)} />
          </label>
          <div className={styles.sessionInfo}>
            <p className="mono wrap">{review.packetName}</p>
            <p role="status" aria-atomic="true">{t.progress(complete, review.cases.length)}</p>
            <progress value={complete} max={review.cases.length} aria-label={t.progress(complete, review.cases.length)} />
          </div>
          <span className={styles.saveState} data-dirty={review.dirty}>{review.dirty ? t.unsaved : ""}</span>
          <p id="review-identity-hint" className={`muted ${styles.sessionHint}`}>{review.identityLocked ? t.identityLocked : t.reviewerNeeded}</p>
        </section>
        <p className={`muted ${styles.privacy}`}>{t.privacy}</p>
        <ReviewNavigation cases={filtered} ratings={review.ratings} selectedId={selected?.case_id ?? ""} disabled={review.busy}
          context={context} onContext={setContext} onSelect={selectCase} />
        {selected ? <div className={styles.workbench}>
          <ReviewEvidence key={selected.case_id} item={selected} />
          <ReviewScoreForm key={`score-${selected.case_id}`} item={selected}
            score={review.ratings[selected.case_id] ?? emptyScore(selected, review.reviewer)}
            disabled={review.busy || !review.reviewer.trim()} onChange={changes => review.updateScore(selected, changes)} />
        </div> : <p className="feedback">{t.noMatches}</p>}
      </> : <section className={`panel ${styles.empty}`}>
        <span className={styles.emptyIcon}><Icon name="quote" size={34} /></span>
        <h2>{t.emptyTitle}</h2><p className="muted">{t.emptyLead}</p>
        <p className={`mono ${styles.sample}`}>{t.sample}</p>
        <p className="muted">{t.privacy}</p>
      </section>}
    </div>
  );
}
