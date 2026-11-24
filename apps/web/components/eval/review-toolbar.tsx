import { useRef } from "react";

import { Icon } from "@/components/ui/icon";
import { vi } from "@/lib/i18n/vi";
import styles from "./review.module.css";

type Props = {
  hasPacket: boolean; busy: boolean; canExport: boolean;
  onImport: (file: File, kind: "packet" | "scores") => void;
  onExport: () => void;
};

export function ReviewToolbar({ hasPacket, busy, canExport, onImport, onExport }: Props) {
  const packet = useRef<HTMLInputElement>(null);
  const scores = useRef<HTMLInputElement>(null);
  const t = vi.review;
  return (
    <div className={styles.toolbar} aria-busy={busy}>
      {([{ kind: "packet", ref: packet }, { kind: "scores", ref: scores }] as const).map(({ kind, ref }) => (
        <input key={kind} ref={ref} type="file" accept=".jsonl" hidden
          aria-label={kind === "packet" ? t.openPacket : t.importScores}
          onChange={event => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (file) onImport(file, kind);
          }} />
      ))}
      <button className={`button ${hasPacket ? "secondary" : "primary"}`} disabled={busy} onClick={() => packet.current?.click()}>
        <Icon name="upload" size={17} />{t.openPacket}
      </button>
      {hasPacket && <>
        <button className="button secondary" disabled={busy} onClick={() => scores.current?.click()}>{t.importScores}</button>
        <button className="button primary" disabled={busy || !canExport} onClick={onExport}>{t.exportScores}</button>
      </>}
    </div>
  );
}
