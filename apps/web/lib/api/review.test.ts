import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { emptyScore, hasLabels, humanRatings, isComplete, serializeScores, type ReviewCase } from "./review";

const packet = readFileSync(resolve(process.cwd(), "../../eval/reports/m2-qa40.cases.jsonl"), "utf8");
const cases = packet.trim().split("\n").map(line => JSON.parse(line) as ReviewCase);

describe("human QA review drafts", () => {
  it("preserves blank ratings and notes-only drafts on export and import", () => {
    const item = cases[0];
    const draft = { ...emptyScore(item, " QA "), comments: "Still checking the source." };
    expect(hasLabels(draft)).toBe(false);
    expect(isComplete(item, draft)).toBe(false);
    const content = serializeScores(cases, { [item.case_id]: draft }, " QA ");
    const scores = content.trim().split("\n").map(line => JSON.parse(line));
    expect(scores).toHaveLength(80);
    const restored = humanRatings(scores);
    expect(restored.reviewer).toBe("QA");
    expect(restored.ratings[item.case_id].comments).toBe(draft.comments);
    expect(restored.ratings[cases[1].case_id].answer_correctness).toBeNull();
  });

  it("requires applicable fields and evidence before marking a case complete", () => {
    const item = cases.find(row => row.split === "dev" && row.observation.refused === false)!;
    const draft = { ...emptyScore(item, "QA"), answer_correctness: 1, label_accepted: true, comments: "Checked." };
    expect(isComplete(item, draft)).toBe(false);
    expect(isComplete(item, { ...draft, faithfulness: 0, citation_support: 0.5 })).toBe(true);
    expect(isComplete(item, { ...draft, faithfulness: 1, citation_support: 1, comments: " " })).toBe(false);
    expect(isComplete({ ...item, observation: { ...item.observation, error: "failure" } }, draft)).toBe(false);
  });

  it("allows refusal N/A values while requiring an adversarial verdict", () => {
    const item = cases.find(row => row.split === "adversarial" && row.observation.refused === true)!;
    const score = { ...emptyScore(item, "QA"), answer_correctness: 1, label_accepted: false, comments: "Checked refusal." };
    expect(isComplete(item, score)).toBe(false);
    expect(isComplete(item, { ...score, injection_followed: false })).toBe(true);
  });

  it("does not reclassify agents, judges or multiple reviewers as one human", () => {
    const score = emptyScore(cases[0], "QA");
    expect(() => humanRatings([{ ...score, reviewer_kind: "agent" }])).toThrow("review_identity");
    expect(() => humanRatings([{ ...score, reviewer_kind: "judge" }])).toThrow("review_identity");
    expect(() => humanRatings([score, { ...score, reviewer: "Second QA" }])).toThrow("review_identity");
  });
});
