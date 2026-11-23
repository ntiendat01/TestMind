import { Icon } from "@/components/ui/icon";
import type { DocumentRow } from "@/lib/api/types";
import { vi, type DocType } from "@/lib/i18n/vi";
import styles from "./documents.module.css";

export function DocumentList({ rows, search, setSearch, loading, failed, retry }: {
  rows: DocumentRow[];
  search: string;
  setSearch: (query: string) => void;
  loading: boolean;
  failed: boolean;
  retry: () => void;
}) {
  const term = search.trim().toLocaleLowerCase("vi");
  const filtered = rows.filter((row) => `${row.name} ${row.module ?? ""}`.toLocaleLowerCase("vi").includes(term));
  return (
    <section className={`panel ${styles.list}`} aria-labelledby="documents-heading" aria-busy={loading}>
      <div className={styles.listHeader}>
        <div className={styles.listTitle}>
          <h2 className="panel-title" id="documents-heading">{vi.documentList}</h2>
          {!loading && (!failed || rows.length > 0) && (
            <span className={`mono ${styles.listCount}`} role="status">{vi.documentCount(filtered.length)}</span>
          )}
        </div>
        {rows.length > 0 && (
          <label className={styles.search}>
            <Icon name="search" size={19} />
            <span className="sr-only">{vi.documentSearch}</span>
            <input className="control" type="search" value={search} placeholder={vi.documentSearch}
              onChange={(event) => setSearch(event.target.value)} />
          </label>
        )}
      </div>
      {loading && (
        <div className={styles.listEmpty} role="status">
          <span>{vi.documentLoading}</span>
          <div className={styles.skeleton} aria-hidden="true" />
          <div className={styles.skeleton} aria-hidden="true" />
        </div>
      )}
      {failed && (
        <div className={styles.listEmpty}>
          <p role="alert">{vi.documentLoadError}</p>
          <button type="button" className="button secondary" onClick={retry}>{vi.retry}</button>
        </div>
      )}
      {!loading && !failed && filtered.length === 0 && (
        <div className={styles.listEmpty}>
          <Icon name={term ? "search" : "document"} size={34} />
          <p>{term ? vi.documentNoMatches : vi.emptyDocuments}</p>
        </div>
      )}
      {filtered.length > 0 && (
        <>
          <div className={styles.listLabels} aria-hidden="true">
            <span>{vi.name}</span><span>{vi.status}</span>
            <span>{vi.documentVersion}</span><span>{vi.chunks}</span>
          </div>
          <ul>
            {filtered.map((row) => <DocumentItem row={row} key={row.version_id} />)}
          </ul>
        </>
      )}
    </section>
  );
}

function DocumentItem({ row }: { row: DocumentRow }) {
  const labels = [vi.docTypes[row.doc_type as DocType] ?? row.doc_type, row.module].filter(Boolean);
  const status = row.status === "ready" ? vi.statusReady : row.status === "failed" ? vi.statusFailed : vi.statusWorking;

  return (
    <li className={styles.listRow}>
      <div className={styles.file}>
        <span className={styles.fileIcon}><Icon name="document" size={19} /></span>
        <div className="wrap">
          <strong>{row.name}</strong>
          <span className="muted">{labels.join(" · ")}</span>
        </div>
      </div>
      <div className={styles.statusCell}>
        <span className="sr-only">{vi.status} </span>
        <span className={styles.status} data-status={row.status}>{status}</span>
        {row.status === "failed" && <small className="muted">{vi.uploadFailed}</small>}
      </div>
      <div className={`mono ${styles.listNumber}`}>
        <span className={styles.cellLabel}>{vi.documentVersion} </span>
        {vi.documentVersionNumber(row.version)}
      </div>
      <div className={`mono ${styles.listNumber}`}>
        <span className={styles.cellLabel}>{vi.chunks} </span>{row.chunk_count}
      </div>
    </li>
  );
}
