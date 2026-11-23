import { describe, expect, it } from "vitest";

import { parseSseBlock } from "./parse";

describe("parseSseBlock", () => {
  it("reads event name and data", () => {
    const parsed = parseSseBlock('event: final\ndata: {"answer":"ok"}');
    expect(parsed).toEqual({ event: "final", data: '{"answer":"ok"}' });
  });

  it("returns null when the block has no data", () => {
    expect(parseSseBlock("event: retrieval")).toBeNull();
  });

  it("joins split data lines", () => {
    const parsed = parseSseBlock("event: error\ndata: one\ndata: two");
    expect(parsed?.data).toBe("one\ntwo");
  });
});
