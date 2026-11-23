import { describe, expect, it } from "vitest";

import { describeLocation, orderEvidence } from "./citations";
import type { Claim, SourceHit } from "./types";

function hit(id: string, loc: SourceHit["loc"] = {}, section_path: string[] = []): SourceHit {
  return { chunk_id: id, score: 0.7, document_name: `${id}.md`, text: id, loc, section_path };
}

function claim(...ids: string[]): Claim {
  return {
    text: "Quy tắc", status: "verified", chunk_ids: ids,
    sources: ids.map((id) => ({
      chunk_id: id, document_name: `${id}.md`, section_path: [], loc: {},
    })),
  };
}

describe("evidence references", () => {
  it("numbers sources by first citation and keeps uncited results available", () => {
    const evidence = orderEvidence([hit("related"), hit("a"), hit("b"), hit("a")], [
      claim("b", "missing", "a"), claim("b"),
    ]);
    expect(evidence.map(({ hit, label, cited }) => [hit.chunk_id, label, cited])).toEqual([
      ["b", "01", true], ["a", "02", true], ["related", "03", false],
    ]);
  });

  it("keeps retrieval order for a refusal with candidate sources", () => {
    expect(orderEvidence([hit("a"), hit("b")], []).map(({ hit, cited }) => [hit.chunk_id, cited]))
      .toEqual([["a", false], ["b", false]]);
  });

  it("describes source locations and avoids repeating an Excel sheet name", () => {
    expect(describeLocation(hit("a", { sheet: "Refund", row: 7 }, ["Refund"])))
      .toEqual(["Sheet Refund", "Dòng 7"]);
    expect(describeLocation(hit("b", { paragraph_idx: 0 }, ["Hoàn tiền", "Điều kiện"])))
      .toEqual(["Hoàn tiền › Điều kiện", "Khối 1"]);
  });
});
