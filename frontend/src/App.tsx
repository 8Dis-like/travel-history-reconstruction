import { useState } from "react";
import type { UploadFileItem } from "./types";
import { extractMockPdf } from "./api";
import { UploadPanel } from "./components/UploadPanel";

function makeId(): string {
  return Math.random().toString(36).slice(2);
}

export default function App() {
  const [files, setFiles] = useState<UploadFileItem[]>([]);

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
        await extractMockPdf(item.file);
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

  return (
    <main>
      <h1>Travel History Reconstruction</h1>
      <UploadPanel files={files} onAddFiles={addFiles} onStartRecognition={startRecognition} />
    </main>
  );
}
