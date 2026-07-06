import type { TimelineEntry } from "./types";

export function partitionEntries(entries: TimelineEntry[]): {
  timeline: TimelineEntry[];
  unreadable: TimelineEntry[];
} {
  const unreadable = entries.filter((entry) => entry.date === null);
  const timeline = entries
    .filter((entry): entry is TimelineEntry & { date: string } => entry.date !== null)
    .slice()
    .sort((a, b) => a.date.localeCompare(b.date));

  return { timeline, unreadable };
}
