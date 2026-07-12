import { describe, expect, it } from "vitest";
import { partitionEntries } from "./partitionEntries";
import type { TimelineEntry } from "./types";

function makeEntry(overrides: Partial<TimelineEntry>): TimelineEntry {
  return {
    id: "id",
    sourceFile: "test.pdf",
    date: null,
    country: null,
    direction: null,
    rawText: null,
    confidence: 0,
    ...overrides,
  };
}

describe("partitionEntries", () => {
  it("sorts entries with a date ascending into the timeline", () => {
    const entries = [
      makeEntry({ id: "b", date: "2024-02-20" }),
      makeEntry({ id: "a", date: "2024-01-10" }),
    ];

    const { timeline } = partitionEntries(entries);

    expect(timeline.map((e) => e.id)).toEqual(["a", "b"]);
  });

  it("puts entries with a null date into unreadable, not timeline", () => {
    const entries = [
      makeEntry({ id: "readable", date: "2024-01-10" }),
      makeEntry({ id: "unreadable", date: null }),
    ];

    const { timeline, unreadable } = partitionEntries(entries);

    expect(timeline.map((e) => e.id)).toEqual(["readable"]);
    expect(unreadable.map((e) => e.id)).toEqual(["unreadable"]);
  });
});
