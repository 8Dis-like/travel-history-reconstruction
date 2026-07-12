import { useState } from "react";
import { Alert, Button, Layout, Space, Typography } from "antd";
import type { TimelineEntry, UploadFileItem } from "./types";
import { extractMockPdf } from "./api";
import { partitionEntries } from "./partitionEntries";
import { UploadPanel } from "./components/UploadPanel";
import { Timeline } from "./components/Timeline";
import { UnreadableList } from "./components/UnreadableList";

const { Content } = Layout;
const { Title } = Typography;

function makeId(): string {
  return Math.random().toString(36).slice(2);
}

const DEMO_FILE_CONTENT = "%PDF-1.4\n%%EOF";

export default function App() {
  const [files, setFiles] = useState<UploadFileItem[]>([]);
  const [entries, setEntries] = useState<TimelineEntry[]>([]);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoError, setDemoError] = useState<string | null>(null);

  function addFiles(newFiles: File[]) {
    const pdfFiles = newFiles.filter((f) => f.type === "application/pdf");
    const items: UploadFileItem[] = pdfFiles.map((file) => ({
      id: makeId(),
      file,
      status: "pending",
    }));
    setFiles((prev) => [...prev, ...items]);
  }

  async function startRecognition() {
    const toProcess = files.filter((f) => f.status === "pending" || f.status === "error");

    for (const item of toProcess) {
      setFiles((prev) =>
        prev.map((f) => (f.id === item.id ? { ...f, status: "processing" } : f))
      );

      try {
        const newEntries = await extractMockPdf(item.file);
        setEntries((prev) => [...prev, ...newEntries]);
        setFiles((prev) =>
          prev.map((f) => (f.id === item.id ? { ...f, status: "done" } : f))
        );
      } catch {
        setFiles((prev) =>
          prev.map((f) => (f.id === item.id ? { ...f, status: "error" } : f))
        );
      }
    }
  }

  async function loadDemoData() {
    setDemoLoading(true);
    setDemoError(null);

    try {
      const demoFile = new File([DEMO_FILE_CONTENT], "demo.pdf", { type: "application/pdf" });
      const newEntries = await extractMockPdf(demoFile);
      setEntries((prev) => [...prev, ...newEntries]);
    } catch {
      setDemoError("Failed to load demo data.");
    } finally {
      setDemoLoading(false);
    }
  }

  const { timeline, unreadable } = partitionEntries(entries);

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Content style={{ maxWidth: 720, margin: "0 auto", padding: 24, width: "100%" }}>
        <Title level={2}>Travel History Reconstruction</Title>
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <UploadPanel files={files} onAddFiles={addFiles} onStartRecognition={startRecognition} />
          <div>
            <Button onClick={loadDemoData} loading={demoLoading}>
              {demoLoading ? "Loading demo data..." : "Load demo data"}
            </Button>
            {demoError && (
              <Alert type="error" message={demoError} showIcon style={{ marginTop: 8 }} />
            )}
          </div>
          <Timeline entries={timeline} />
          <UnreadableList entries={unreadable} />
        </Space>
      </Content>
    </Layout>
  );
}
