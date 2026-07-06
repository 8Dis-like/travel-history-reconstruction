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
      <h2>无法识别</h2>
      <ul>
        {entries.map((entry) => (
          <li key={entry.id}>{entry.sourceFile}：该图片不可识别</li>
        ))}
      </ul>
    </section>
  );
}
