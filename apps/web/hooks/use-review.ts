"use client";

import { useEffect, useRef, useState } from "react";

import { ApiError, validateReviewPacket, validateReviewScores } from "@/lib/api/client";
import { emptyScore, hasLabels, humanRatings, serializeScores, type Ratings, type ReviewCase, type ReviewScore } from "@/lib/api/review";
import { vi } from "@/lib/i18n/vi";

const t = vi.review;

async function readFile(file: File): Promise<string> {
  if (!file.name.endsWith(".jsonl") || file.size > 5_000_000 || !file.size) throw new Error("file");
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
  } catch {
    throw new Error("file");
  }
}

function messageFor(error: unknown, kind: "packet" | "scores"): string {
  if (error instanceof Error && error.message === "file") return t.invalidFile;
  if (error instanceof Error && error.message === "review_identity") return t.identityError;
  if (error instanceof ApiError) return kind === "packet" ? t.packetError : t.scoresError;
  return t.networkError;
}

export function useReview() {
  const [cases, setCases] = useState<ReviewCase[]>([]);
  const [ratings, setRatings] = useState<Ratings>({});
  const [reviewer, setReviewer] = useState("");
  const [packetName, setPacketName] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [needsReasons, setNeedsReasons] = useState<string[]>([]);
  const running = useRef(false);

  useEffect(() => {
    if (!dirty) return;
    function beforeUnload(event: BeforeUnloadEvent) { event.preventDefault(); }
    function beforeLink(event: MouseEvent) {
      const anchor = event.target instanceof Element ? event.target.closest("a[href]") : null;
      if (!(anchor instanceof HTMLAnchorElement) || anchor.target === "_blank" || anchor.download) return;
      const url = new URL(anchor.href);
      if (url.pathname === location.pathname && url.origin === location.origin && url.hash) return;
      if (!window.confirm(t.replace)) { event.preventDefault(); event.stopPropagation(); }
    }
    window.addEventListener("beforeunload", beforeUnload);
    document.addEventListener("click", beforeLink, true);
    return () => {
      window.removeEventListener("beforeunload", beforeUnload);
      document.removeEventListener("click", beforeLink, true);
    };
  }, [dirty]);

  async function importFile(file: File, kind: "packet" | "scores") {
    if (running.current || (dirty && !window.confirm(t.replace))) return;
    running.current = true;
    setBusy(true); setError(""); setNotice("");
    try {
      const content = await readFile(file);
      if (kind === "packet") {
        const imported = await validateReviewPacket(content);
        setCases(imported); setRatings({}); setReviewer("");
        setPacketName(file.name); setSelectedId(imported[0].case_id);
        setNotice(t.loaded);
      } else {
        const imported = humanRatings(await validateReviewScores(cases, content));
        setRatings(imported.ratings); setReviewer(imported.reviewer); setNotice(t.imported);
      }
      setDirty(false); setNeedsReasons([]);
    } catch (failure) {
      setError(messageFor(failure, kind));
    } finally {
      running.current = false; setBusy(false);
    }
  }

  function updateScore(item: ReviewCase, changes: Partial<ReviewScore>) {
    setRatings(previous => ({ ...previous, [item.case_id]: {
      ...(previous[item.case_id] ?? emptyScore(item, reviewer)), ...changes, reviewer: reviewer.trim(),
    } }));
    setDirty(true); setNotice(""); setNeedsReasons([]);
  }

  async function exportScores() {
    if (running.current) return;
    const missing = cases.filter(item => hasLabels(ratings[item.case_id]) && !ratings[item.case_id].comments.trim());
    setError(""); setNotice(""); setNeedsReasons(missing.map(item => item.case_id));
    if (missing.length) return;
    running.current = true; setBusy(true);
    try {
      const content = serializeScores(cases, ratings, reviewer);
      const validated = await validateReviewScores(cases, content);
      const blob = new Blob([validated.map(score => JSON.stringify(score)).join("\n") + "\n"], { type: "application/x-ndjson;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url; link.download = "review-scores.jsonl";
      document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setDirty(false); setNotice(t.exported);
    } catch (failure) {
      setError(messageFor(failure, "scores"));
    } finally {
      running.current = false; setBusy(false);
    }
  }

  return {
    cases, ratings, reviewer, packetName, selectedId, dirty, busy, error, notice, needsReasons,
    identityLocked: Object.values(ratings).some(hasLabels),
    setSelectedId, importFile, updateScore, exportScores,
    changeReviewer(value: string) { setReviewer(value); setDirty(true); setNotice(""); },
  };
}
