import { useState } from "react";
import type { TimelineEntry, UploadFileItem } from "./types";
import { extractMockPdf } from "./api";
import { partitionEntries } from "./partitionEntries";
import { UploadPanel } from "./components/UploadPanel";
import { Timeline } from "./components/Timeline";
import { UnreadableList } from "./components/UnreadableList";

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
    <main>
      <h1>Travel History Reconstruction</h1>
      <UploadPanel files={files} onAddFiles={addFiles} onStartRecognition={startRecognition} />
      <section className="demo-data">
        <button type="button" onClick={loadDemoData} disabled={demoLoading}>
          {demoLoading ? "Loading demo data..." : "Load demo data"}
        </button>
        {demoError && <p className="demo-error">{demoError}</p>}
      </section>
      <Timeline entries={timeline} />
      <UnreadableList entries={unreadable} />
    </main>
  );
}
