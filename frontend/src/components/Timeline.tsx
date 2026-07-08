import { Empty, Timeline as AntTimeline, Typography } from "antd";
import type { TimelineEntry } from "../types";

interface TimelineProps {
  entries: TimelineEntry[];
}

export function Timeline({ entries }: TimelineProps) {
  if (entries.length === 0) {
    return <Empty description="No results yet" />;
  }

  return (
    <AntTimeline
      mode="alternate"
      items={entries.map((entry) => ({
        key: entry.id,
        label: entry.date,
        children: (
          <>
            <div>
              {entry.country} · {entry.direction} · {Math.round(entry.confidence * 100)}%
            </div>
            <Typography.Text type="secondary">{entry.sourceFile}</Typography.Text>
          </>
        ),
      }))}
    />
  );
}
