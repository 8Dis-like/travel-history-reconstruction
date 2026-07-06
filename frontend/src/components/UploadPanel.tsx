import { useRef } from "react";
import type { ChangeEvent, DragEvent } from "react";
import type { UploadFileItem } from "../types";

interface UploadPanelProps {
  files: UploadFileItem[];
  onAddFiles: (files: File[]) => void;
  onStartRecognition: () => void;
}

export function UploadPanel({ files, onAddFiles, onStartRecognition }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files ?? []);
    onAddFiles(selected);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    const dropped = Array.from(event.dataTransfer.files);
    onAddFiles(dropped);
  }

  const hasProcessable = files.some((f) => f.status === "pending" || f.status === "error");
  const isRecognizing = files.some((f) => f.status === "processing");

  return (
    <section className="upload-panel">
      <div
        className="upload-dropzone"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <p>拖拽 PDF 到这里，或点击选择文件</p>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          multiple
          hidden
          onChange={handleFileInputChange}
        />
      </div>

      <ul className="upload-file-list">
        {files.map((item) => (
          <li key={item.id}>
            <span>{item.file.name}</span>
            <span className={`status status-${item.status}`}>{item.status}</span>
          </li>
        ))}
      </ul>

      <button type="button" disabled={!hasProcessable || isRecognizing} onClick={onStartRecognition}>
        开始识别
      </button>
    </section>
  );
}
