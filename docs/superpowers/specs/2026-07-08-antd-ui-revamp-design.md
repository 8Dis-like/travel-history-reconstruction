# Ant Design UI Revamp — Design

## Context

The `frontend/` app (Vite + React 18 + TypeScript) currently renders the
upload panel, timeline, and unreadable-entries list with hand-written CSS
(`frontend/src/styles.css`) and no component library. The user finds the
current look unpolished and wants to swap in a ready-made component library
rather than continue hand-styling.

This is a pure presentation-layer change: no business logic, state
management, or API contracts are affected.

## Goals

- Replace hand-rolled markup/CSS in `App.tsx`, `UploadPanel.tsx`,
  `Timeline.tsx`, and `UnreadableList.tsx` with Ant Design (antd v5)
  components.
- Keep all existing state/data flow (`useState` in `App.tsx`,
  `partitionEntries.ts`, `api.ts`) unchanged.
- Use antd's default theme (no color customization, no dark mode).

## Non-Goals

- No changes to backend, mock data shape, or upload/recognition behavior.
- No dark mode / theme switching.
- No new component-level tests — existing `partitionEntries.test.ts` is the
  only automated frontend test and is unaffected since it tests a pure
  function, not rendering.

## Dependencies

Add to `frontend/package.json`:
- `antd` (v5 — CSS-in-JS, no separate stylesheet/less build step needed)
- `@ant-design/icons`

## Setup

`frontend/src/main.tsx` wraps `<App />` in antd's `<ConfigProvider>` with no
custom `theme` prop (default theme).

## Component Mapping

### `App.tsx`
- Replace bare `<main><h1>` with antd `Layout` and `Typography.Title` for
  the page shell and "Travel History Reconstruction" heading.
- The "Load demo data" button/error block stays in `App.tsx`, restyled with
  antd `Button` (loading state while `demoLoading`) and `Alert
  type="error"` for `demoError`.

### `UploadPanel.tsx`
- Dropzone becomes antd `Upload.Dragger` (`beforeUpload` returns `false` to
  keep the existing manual-trigger flow — no auto-upload on drop).
- File list becomes an antd `List`, one `List.Item` per `UploadFileItem`,
  with a `Tag` showing status (`pending` = default, `processing` = blue,
  `done` = green, `error` = red) — mirrors the current
  `.status-pending/.status-processing/.status-done/.status-error` CSS
  classes.
- "开始识别" trigger becomes `Button type="primary" loading={...}`,
  disabled while a batch is in-flight (existing behavior preserved).

### `Timeline.tsx`
- Replace the hand-built center-line/flex layout with antd `Timeline`
  using `mode="alternate"`, which natively gives the current left/right
  alternating look.
- Each `TimelineEntry` becomes a `Timeline.Item` with the date as the
  label and country/direction/source file in the item body.

### `UnreadableList.tsx`
- Section heading "Unrecognizable" becomes an `Alert type="warning"
  showIcon` banner.
- Entries become an antd `List` of `List.Item`s (one line per entry, same
  `"{sourceFile}: this file could not be recognized"` text as today).
- Keep the existing `return null` when `entries.length === 0`.

## Styling Cleanup

`frontend/src/styles.css` loses all component-specific rules (`.timeline`,
`.timeline-card`, `.timeline-left/right`, `.upload-dropzone`,
`.upload-file-list`, `.status-*`, `.unreadable-list`, `.demo-error`) since
antd components own their own styling. What remains: page-level layout
(max-width/centering) if `Layout` doesn't already cover it.

## Testing / Verification

- `frontend/src/partitionEntries.test.ts` — no changes needed, still green.
- Manual verification: run `npm run dev`, exercise upload → recognize →
  timeline/unreadable-list render, and the "Load demo data" path, checking
  visually that antd components render correctly and existing interaction
  behavior (disabled buttons while in-flight, error states) still works.
- `npm run build` (`tsc --noEmit && vite build`) must pass with the new
  dependency.
