import type { TimelineEntry } from "../types";

interface TimelineProps {
  entries: TimelineEntry[];
}

export function Timeline({ entries }: TimelineProps) {
  if (entries.length === 0) {
    return <p className="timeline-empty">No results yet</p>;
  }

  return (
    <ol className="timeline">
      {entries.map((entry, index) => (
        <li key={entry.id} className={index % 2 === 0 ? "timeline-left" : "timeline-right"}>
          <div className="timeline-card">
            <div className="timeline-date">{entry.date}</div>
            <div>
              {entry.country} · {entry.direction} · {Math.round(entry.confidence * 100)}%
            </div>
            <div className="timeline-source">{entry.sourceFile}</div>
          </div>
        </li>
      ))}
    </ol>
  );
}
