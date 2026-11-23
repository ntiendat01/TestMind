import type { Claim, SourceHit } from "./types";
import { vi } from "@/lib/i18n/vi";

export type Evidence = { hit: SourceHit; label: string; cited: boolean };

export function orderEvidence(hits: SourceHit[], claims: Claim[]): Evidence[] {
  const firstHits = new Map<string, SourceHit>();
  for (const hit of hits) {
    if (!firstHits.has(hit.chunk_id)) firstHits.set(hit.chunk_id, hit);
  }
  const cited = new Set(claims.flatMap((claim) => claim.sources.map((source) => source.chunk_id)));
  const primary = [...cited].flatMap((id) => {
    const hit = firstHits.get(id);
    return hit ? [hit] : [];
  });
  const remaining = [...firstHits.values()].filter((hit) => !cited.has(hit.chunk_id));
  return [...primary, ...remaining].map((hit, index) => ({
    hit,
    label: String(index + 1).padStart(2, "0"),
    cited: cited.has(hit.chunk_id),
  }));
}

export function describeLocation({ section_path: path, loc }: SourceHit): string[] {
  const location = [];
  const sheet = typeof loc.sheet === "string" ? loc.sheet : "";
  const section = path.join(" › ");
  if (section && section !== sheet) location.push(section);
  if (sheet) location.push(vi.sourceSheet(sheet));
  if (typeof loc.page === "number") location.push(vi.sourcePage(loc.page));
  if (typeof loc.paragraph_idx === "number") location.push(vi.sourceBlock(loc.paragraph_idx));
  if (typeof loc.row === "number") location.push(vi.sourceRow(loc.row));
  return location;
}
