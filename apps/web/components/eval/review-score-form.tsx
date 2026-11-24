import { scoreFields, type LabelField, type ReviewCase, type ReviewScore } from "@/lib/api/review";
import { vi } from "@/lib/i18n/vi";
import styles from "./review.module.css";

type Props = {
  item: ReviewCase; score: ReviewScore; disabled: boolean;
  onChange: (changes: Partial<ReviewScore>) => void;
};

export function ReviewScoreForm({ item, score, disabled, onChange }: Props) {
  const t = vi.review;
  const refusal = item.observation.refused === true;
  function select(key: LabelField, value: string) {
    onChange({ [key]: value === "" ? null : key === "injection_followed" || key === "label_accepted" ? value === "true" : Number(value) });
  }
  return (
    <section className={`panel ${styles.scorePanel}`} aria-labelledby="score-title">
      <div className={styles.sectionHead}><span className={styles.eyebrow}>{t.eyebrow}</span><h2 className="panel-title" id="score-title" tabIndex={-1}>{t.scoreTitle}</h2></div>
      <details className={styles.rubric}>
        <summary>{t.rubric}</summary><p>{t.rubricText}</p>
      </details>
      <fieldset disabled={disabled} className={styles.scoreFields}>
        {scoreFields.map(key => {
          const unavailable = !!item.observation.error || (refusal && key !== "answer_correctness");
          return <label className="field" key={key}>{t[key]}
            <select className="control" value={score[key] ?? ""} disabled={unavailable} onChange={event => select(key, event.target.value)}>
              <option value="">{unavailable ? t.notApplicable : t.unscored}</option>
              <option value="1">1</option><option value="0.5">0,5</option><option value="0">0</option>
            </select>
          </label>;
        })}
        {(["label_accepted", "injection_followed"] as const).filter(key => key !== "injection_followed" || item.split === "adversarial").map(key => (
          <label className="field" key={key}>{t[key]}
            <select className="control" value={score[key] == null ? "" : String(score[key])} onChange={event => select(key, event.target.value)}>
              <option value="">{t.unscored}</option><option value="true">{t.yes}</option><option value="false">{t.no}</option>
            </select>
          </label>
        ))}
        <label className="field">{t.comments}
          <textarea id="review-comments" className="control" rows={5} value={score.comments} placeholder={t.commentsPlaceholder}
            onChange={event => onChange({ comments: event.target.value })} />
        </label>
      </fieldset>
    </section>
  );
}
