import { isComplete, type Ratings, type ReviewCase } from "@/lib/api/review";
import { vi } from "@/lib/i18n/vi";
import styles from "./review.module.css";

type Props = {
  cases: ReviewCase[]; ratings: Ratings; selectedId: string; disabled: boolean;
  context: string; onContext: (value: string) => void; onSelect: (id: string) => void;
};

export function ReviewNavigation({ cases, ratings, selectedId, disabled, context, onContext, onSelect }: Props) {
  const t = vi.review;
  const index = cases.findIndex(item => item.case_id === selectedId);
  return (
    <div className={styles.navigator}>
      <label className="field">{t.filter}
        <select className="control" value={context} disabled={disabled} onChange={event => onContext(event.target.value)}>
          <option value="all">{t.all}</option><option value="retrieved">{t.retrieved}</option><option value="gold">{t.gold}</option>
        </select>
      </label>
      <label className={`field ${styles.caseSelect}`}>{t.selectCase}
        <select className="control" value={selectedId} disabled={disabled || !cases.length} onChange={event => onSelect(event.target.value)}>
          {cases.map((item, i) => <option key={item.case_id} value={item.case_id}>
            {i + 1}. {item.observation.id} · {item.observation.context === "gold" ? t.gold : t.retrieved} · {isComplete(item, ratings[item.case_id]) ? t.complete : t.pending} · {item.observation.question}
          </option>)}
        </select>
      </label>
      <div className={styles.steps}>
        <button className="button secondary" disabled={disabled || index <= 0} onClick={() => onSelect(cases[index - 1].case_id)}>{t.previous}</button>
        <button className="button secondary" disabled={disabled || index < 0 || index >= cases.length - 1} onClick={() => onSelect(cases[index + 1].case_id)}>{t.next}</button>
      </div>
    </div>
  );
}
