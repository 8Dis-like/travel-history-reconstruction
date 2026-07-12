# Ant Design UI Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the frontend's hand-rolled CSS/markup with Ant Design v5 components, giving the app a polished, ready-made look without changing any business logic.

**Architecture:** Swap the render layer of `App.tsx`, `UploadPanel.tsx`, `Timeline.tsx`, and `UnreadableList.tsx` to use antd components (`Layout`, `Upload.Dragger`, `Timeline`, `List`, `Alert`, `Button`, `Typography`, `Empty`, `Tag`), wired up once via `ConfigProvider` in `main.tsx`. State (`useState` in `App.tsx`), the pure `partitionEntries` function, and `api.ts` are untouched — only what those files render changes.

**Tech Stack:** React 18 / TypeScript 5 / Vite 5 (existing), antd v5 + `@ant-design/icons` (new).

## Global Constraints

- No backend changes and no changes to `partitionEntries.ts` / `api.ts` / any `useState` logic in `App.tsx` — this is a presentation-only revamp (spec Goals/Non-Goals).
- Use antd's default theme — no color customization, no dark mode (spec Setup).
- `frontend/src/partitionEntries.test.ts` must stay green through every task (spec Testing/Verification).
- `npm run build` (`tsc --noEmit && vite build`, run from `frontend/`) must pass after every task (spec Testing/Verification).
- No new automated component/UI tests are added — antd rendering is verified manually via `npm run dev` (spec Testing/Verification).
- Design reference: `docs/superpowers/specs/2026-07-08-antd-ui-revamp-design.md`.

---

## Task 1: Install antd and wire ConfigProvider

**Files:**
- Modify: `frontend/package.json` (via `npm install`, not hand-edited)
- Modify: `frontend/src/main.tsx`

**Interfaces:**
- Produces: antd's `ConfigProvider` now wraps `<App />` with default theme — every component task after this can import from `"antd"` / `"@ant-design/icons"`.

- [ ] **Step 1: Install dependencies**

Run from `frontend/`:
```bash
cd frontend && npm install antd @ant-design/icons
```
Expected: `package.json` gains `antd` and `@ant-design/icons` under `dependencies`; `package-lock.json` updates; no errors.

- [ ] **Step 2: Wrap the app in ConfigProvider**

Replace `frontend/src/main.tsx` with:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider } from "antd";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider>
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
```

- [ ] **Step 3: Verify the build**

Run: `cd frontend && npm run build`
Expected: `tsc --noEmit` and `vite build` both succeed with no errors.

- [ ] **Step 4: Verify existing tests still pass**

Run: `cd frontend && npm test`
Expected: `partitionEntries.test.ts` passes (unaffected by this change).

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/main.tsx
git commit -m "chore(frontend): add antd and wire ConfigProvider"
```

---

## Task 2: Revamp UploadPanel with antd Dragger/List/Tag/Button

**Files:**
- Modify: `frontend/src/components/UploadPanel.tsx`

**Interfaces:**
- Consumes: `UploadFileItem`, `UploadStatus` from `frontend/src/types.ts` (unchanged); antd from Task 1.
- Produces: `UploadPanel` keeps the exact same props signature `{ files: UploadFileItem[]; onAddFiles: (files: File[]) => void; onStartRecognition: () => void }` — `App.tsx` does not need to change how it calls this component.

- [ ] **Step 1: Replace the component**

Replace `frontend/src/components/UploadPanel.tsx` with:

```tsx
import { InboxOutlined } from "@ant-design/icons";
import { Button, List, Tag, Upload } from "antd";
import type { UploadProps } from "antd";
import type { UploadFileItem, UploadStatus } from "../types";

const { Dragger } = Upload;

interface UploadPanelProps {
  files: UploadFileItem[];
  onAddFiles: (files: File[]) => void;
  onStartRecognition: () => void;
}

const STATUS_COLOR: Record<UploadStatus, string> = {
  pending: "default",
  processing: "processing",
  done: "success",
  error: "error",
};

export function UploadPanel({ files, onAddFiles, onStartRecognition }: UploadPanelProps) {
  const hasProcessable = files.some((f) => f.status === "pending" || f.status === "error");
  const isRecognizing = files.some((f) => f.status === "processing");

  const draggerProps: UploadProps = {
    multiple: true,
    accept: "application/pdf",
    showUploadList: false,
    beforeUpload: (file) => {
      onAddFiles([file]);
      return false;
    },
  };

  return (
    <section className="upload-panel">
      <Dragger {...draggerProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">Drag PDFs here, or click to select files</p>
      </Dragger>

      <List
        style={{ margin: "16px 0" }}
        dataSource={files}
        renderItem={(item) => (
          <List.Item key={item.id}>
            <List.Item.Meta title={item.file.name} />
            <Tag color={STATUS_COLOR[item.status]}>{item.status}</Tag>
          </List.Item>
        )}
      />

      <Button
        type="primary"
        disabled={!hasProcessable || isRecognizing}
        loading={isRecognizing}
        onClick={onStartRecognition}
      >
        Start recognition
      </Button>
    </section>
  );
}
```

- [ ] **Step 2: Verify the build**

Run: `cd frontend && npm run build`
Expected: passes with no type errors (confirms `UploadPanelProps` still matches how `App.tsx` calls `<UploadPanel files={files} onAddFiles={addFiles} onStartRecognition={startRecognition} />`).

- [ ] **Step 3: Verify existing tests still pass**

Run: `cd frontend && npm test`
Expected: `partitionEntries.test.ts` passes.

- [ ] **Step 4: Manual check**

Run: `cd frontend && npm run dev`, open the printed local URL.
Expected: dragging a PDF onto the dragzone (or clicking it to pick a file) adds it to the list below with a "pending" tag; "Start recognition" is disabled until at least one pending/error file exists, and shows a loading spinner while a batch is in-flight (mirrors prior behavior).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/UploadPanel.tsx
git commit -m "feat(frontend): revamp UploadPanel with antd Dragger/List/Tag"
```

---

## Task 3: Revamp Timeline with antd Timeline (alternate mode)

**Files:**
- Modify: `frontend/src/components/Timeline.tsx`

**Interfaces:**
- Consumes: `TimelineEntry` from `frontend/src/types.ts` (unchanged).
- Produces: `Timeline` keeps the exact same props signature `{ entries: TimelineEntry[] }` — `App.tsx` calls it unchanged as `<Timeline entries={timeline} />`.

- [ ] **Step 1: Replace the component**

Replace `frontend/src/components/Timeline.tsx` with:

```tsx
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
```

- [ ] **Step 2: Verify the build**

Run: `cd frontend && npm run build`
Expected: passes with no type errors.

- [ ] **Step 3: Verify existing tests still pass**

Run: `cd frontend && npm test`
Expected: `partitionEntries.test.ts` passes.

- [ ] **Step 4: Manual check**

Run: `cd frontend && npm run dev`, click "Load demo data" (or upload + recognize).
Expected: dated entries render as an antd alternating timeline (left/right around a center line); with zero entries, an antd `Empty` placeholder with text "No results yet" shows instead.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/Timeline.tsx
git commit -m "feat(frontend): revamp Timeline with antd alternate Timeline"
```

---

## Task 4: Revamp UnreadableList with antd Alert + List

**Files:**
- Modify: `frontend/src/components/UnreadableList.tsx`

**Interfaces:**
- Consumes: `TimelineEntry` from `frontend/src/types.ts` (unchanged).
- Produces: `UnreadableList` keeps the exact same props signature `{ entries: TimelineEntry[] }` — `App.tsx` calls it unchanged as `<UnreadableList entries={unreadable} />`.

- [ ] **Step 1: Replace the component**

Replace `frontend/src/components/UnreadableList.tsx` with:

```tsx
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
```

- [ ] **Step 2: Verify the build**

Run: `cd frontend && npm run build`
Expected: passes with no type errors.

- [ ] **Step 3: Verify existing tests still pass**

Run: `cd frontend && npm test`
Expected: `partitionEntries.test.ts` passes.

- [ ] **Step 4: Manual check**

Run: `cd frontend && npm run dev`, click "Load demo data".
Expected: the fixed mock record with a null date renders under a warning-styled "Unrecognizable" banner with an antd `List` item reading "demo.pdf: this file could not be recognized"; section renders nothing when `unreadable` is empty.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/UnreadableList.tsx
git commit -m "feat(frontend): revamp UnreadableList with antd Alert/List"
```

---

## Task 5: Revamp App shell and clean up styles.css

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`

**Interfaces:**
- Consumes: `UploadPanel`, `Timeline`, `UnreadableList` (all from Tasks 2-4, same prop signatures as before); `TimelineEntry`, `UploadFileItem` from `types.ts`; `extractMockPdf` from `api.ts`; `partitionEntries` from `partitionEntries.ts`. None of these change.

- [ ] **Step 1: Replace App.tsx**

Replace `frontend/src/App.tsx` with:

```tsx
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
```

- [ ] **Step 2: Strip component-specific CSS**

Replace `frontend/src/styles.css` with:

```css
body {
  margin: 0;
}
```

All layout/spacing that used to live in `.upload-dropzone`, `.upload-file-list`, `.status-*`, `.timeline`, `.timeline-left/right`, `.timeline-card`, `.timeline-source`, `.timeline-empty`, `.unreadable-list`, `.demo-data`, `.demo-error` is now handled by antd components (`Dragger`, `List`, `Tag`, `Timeline`, `Empty`, `Typography.Text`, `Alert`) or inline styles on `Layout`/`Content`/`Space` in `App.tsx`.

- [ ] **Step 3: Verify the build**

Run: `cd frontend && npm run build`
Expected: passes with no type errors.

- [ ] **Step 4: Verify existing tests still pass**

Run: `cd frontend && npm test`
Expected: `partitionEntries.test.ts` passes.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/styles.css
git commit -m "feat(frontend): revamp App shell with antd Layout and clean up styles.css"
```

---

## Task 6: End-to-end manual verification

**Files:** none (verification only, no commit expected).

- [ ] **Step 1: Start the app**

Run: `cd frontend && npm run dev` (ensure the FastAPI backend is also running so `/api/*` proxy calls succeed, e.g. `uvicorn src.api.main:app --reload` from the repo root in a separate terminal).

- [ ] **Step 2: Exercise the upload → recognize flow**

In the browser: drag a PDF onto the antd Dragger (or click to pick one) → confirm it appears in the file list with a "pending" `Tag` → click "Start recognition" → confirm the button shows a loading state, the file's tag transitions to "processing" then "done", three dated entries appear in the alternating antd `Timeline`, and one "Unrecognizable" entry appears under the warning `Alert`.

- [ ] **Step 3: Exercise the demo-data flow**

Click "Load demo data" → confirm the button shows a loading state and the same timeline/unreadable-list entries appear (accumulating alongside any entries from Step 2, matching existing accumulation behavior).

- [ ] **Step 4: Confirm final build/test state**

Run: `cd frontend && npm run build && npm test`
Expected: both succeed — this is the final confirmation that the revamp is complete and nothing regressed.
