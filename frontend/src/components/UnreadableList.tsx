import { Alert, List } from "antd";
import type { TimelineEntry } from "../types";

interface UnreadableListProps {
  entries: TimelineEntry[];
}

export function UnreadableList({ entries }: UnreadableListProps) {
  if (entries.length === 0) {
    return null;
  }

  return (
    <section>
      <Alert type="warning" showIcon message="Unrecognizable" style={{ marginBottom: 8 }} />
      <List
        dataSource={entries}
        renderItem={(entry) => (
          <List.Item key={entry.id}>{entry.sourceFile}: this file could not be recognized</List.Item>
        )}
      />
    </section>
  );
}
