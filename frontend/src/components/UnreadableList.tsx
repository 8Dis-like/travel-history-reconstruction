import type { TimelineEntry } from "../types";

interface UnreadableListProps {
  entries: TimelineEntry[];
}

export function UnreadableList({ entries }: UnreadableListProps) {
  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="unreadable-list">
      <h2>Unrecognizable</h2>
      <ul>
        {entries.map((entry) => (
          <li key={entry.id}>{entry.sourceFile}: this file could not be recognized</li>
        ))}
      </ul>
    </section>
  );
}
