import type { RefObject } from "react";

import { Icon } from "@/components/ui/icon";
import { describeLocation, type Evidence } from "@/lib/api/citations";
import { vi } from "@/lib/i18n/vi";
import styles from "./chat.module.css";

export function SourcePanel({ panel, sources, selectedId, onSelect, onReturn, noResults }: {
  panel: RefObject<HTMLElement | null>;
  sources: Evidence[];
  selectedId: string;
  onSelect: (id: string) => void;
  onReturn?: () => void;
  noResults: boolean;
}) {
  const active = sources.find((item) => item.hit.chunk_id === selectedId);
  return (
    <aside ref={panel} tabIndex={-1} id="source-panel" aria-labelledby="source-title"
      className={`panel ${styles.source}`}>
      <div className={styles.panelHead}>
        <span className={styles.panelIcon}><Icon name="quote" size={22} /></span>
        <h2 id="source-title" className="panel-title">{vi.sourceTitle}</h2>
        {sources.length > 0 && <span className={`mono ${styles.sourceCount}`}>{vi.sourceCount(sources.length)}</span>}
      </div>
      {active ? (
        <div className={styles.sourceBody}>
          <div className="sr-only" role="status">{vi.sourceIndex(active.label)} {active.hit.document_name}</div>
          {onReturn && <button type="button" className={styles.sourceReturn} onClick={onReturn}>{vi.sourceBack}</button>}
          <SourceExcerpt item={active} />
          {sources.length > 1 && (
            <details open={sources.length <= 3} className={styles.sourceChoices}>
              <summary>{vi.sourceList}</summary>
              <ul>
                {sources.map((item) => (
                  <li key={item.hit.chunk_id}>
                    <button type="button" aria-pressed={selectedId === item.hit.chunk_id}
                      onClick={() => onSelect(item.hit.chunk_id)}>
                      <span className="mono">{item.label}</span>
                      <span className="wrap">
                        {item.hit.document_name}
                        <small>{describeLocation(item.hit).join(" · ") || (item.cited ? vi.sourceCited : vi.sourceRelated)}</small>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      ) : (
        <div className={styles.emptySource}>
          <div className={styles.paperStack} aria-hidden="true"><Icon name="document" size={31} /></div>
          <strong>{vi.sourceEmptyTitle}</strong>
          <p>{noResults ? vi.noSourceFound : vi.sourceEmpty}</p>
        </div>
      )}
    </aside>
  );
}

function SourceExcerpt({ item }: { item: Evidence }) {
  const location = describeLocation(item.hit);
  return (
    <section aria-label={vi.sourceIndex(item.label)} className={styles.excerpt}>
      <div className={styles.excerptMeta}>
        <span className={`mono ${styles.reference}`}>{item.label}</span>
        <span>{item.cited ? vi.sourceCited : vi.sourceRelated}</span>
      </div>
      <h3 className="wrap">{item.hit.document_name}</h3>
      {location.length > 0 && (
        <p className={styles.location}>
          <span className="sr-only">{vi.sourceLocated}{" "}</span>{location.join(" · ")}
        </p>
      )}
      <blockquote className="wrap">{item.hit.text}</blockquote>
    </section>
  );
}
