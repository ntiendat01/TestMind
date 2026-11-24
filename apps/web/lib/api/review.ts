import type { components } from "./schema";

export type ReviewCase = components["schemas"]["ReviewCase"];
export type ReviewScore = components["schemas"]["ReviewScore"];
export type Ratings = Record<string, ReviewScore>;
export const scoreFields = ["faithfulness", "answer_correctness", "citation_support"] as const;
export const labelFields = [...scoreFields, "injection_followed", "label_accepted"] as const;
export type LabelField = typeof labelFields[number];

export function emptyScore(item: ReviewCase, reviewer: string): ReviewScore {
  return {
    case_id: item.case_id, observation_sha256: item.observation_sha256,
    reviewer: reviewer.trim(), reviewer_kind: "human", comments: "",
    faithfulness: null, answer_correctness: null, citation_support: null,
    injection_followed: null, label_accepted: null,
  };
}

export function hasLabels(score?: ReviewScore): boolean {
  return !!score && labelFields.some(key => score[key] != null);
}

export function isComplete(item: ReviewCase, score?: ReviewScore): boolean {
  if (!score || !score.reviewer.trim() || !score.comments.trim() || item.observation.error) return false;
  if (score.answer_correctness == null || score.label_accepted == null) return false;
  if (item.observation.refused === false && (score.faithfulness == null || score.citation_support == null)) return false;
  return item.split !== "adversarial" || score.injection_followed != null;
}

export function serializeScores(cases: ReviewCase[], ratings: Ratings, reviewer: string): string {
  return cases.map(item => JSON.stringify({
    ...(ratings[item.case_id] ?? emptyScore(item, reviewer)), reviewer: reviewer.trim(),
  })).join("\n") + "\n";
}

export function humanRatings(scores: ReviewScore[]): { reviewer: string; ratings: Ratings } {
  const names = new Set(scores.map(score => score.reviewer.trim()).filter(Boolean));
  if (names.size > 1 || scores.some(score => score.reviewer_kind !== "human")) {
    throw new Error("review_identity");
  }
  return { reviewer: [...names][0] ?? "", ratings: Object.fromEntries(scores.map(score => [score.case_id, score])) };
}

export function textValue(value: unknown): string {
  return typeof value === "string" ? value : "";
}

export function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}
