# PDF Upload + Mock Timeline Frontend Design

**Date:** 2026-07-06
**Owner:** Zuyan Tao
**Stage:** Frontend prototype, ahead of real recognition module (Stage 2/3)

---

## 1. Problem

The real recognition pipeline (`ClaudeExtractor`, detection) is still being built out. We need a frontend that lets a user upload multiple passport PDFs — possibly in separate batches over time — and see the resulting travel history rendered as a chronological timeline, so the upload/timeline UX can be built and demoed now without waiting on the real backend. The recognition step is faked with a canned backend response; swapping in the real module later should only require replacing that one endpoint's implementation.

## 2. Scope

In scope:
- Multi-file PDF upload, accumulated across multiple upload actions within one browser session
- Manual "开始识别" (start recognition) trigger — user can add more files, then trigger processing again
- A new backend mock endpoint that returns fixed, hardcoded fake extraction results (no real PDF parsing)
- A vertical, center-line, left/right-alternating timeline sorted by date
- A separate "不可识别" (unrecognizable) list for records with no date

Out of scope (deferred):
- Cross-session/persistent storage of uploaded files or results
- Data quality summary panel, CSV/JSON export, stamp gallery
- Real PDF content parsing (page rendering, page count, etc.)
- Auth, multi-user/multi-subject separation

## 3. Architecture

New `frontend/` directory: Vite + React + TypeScript, single-page app, no routing needed.

Dev workflow: Vite dev server on port 5173 proxies `/api/*` to the existing FastAPI app on port 8000. FastAPI enables CORS for the Vite dev origin. Production static-hosting of the built frontend is out of scope for this iteration (noted as a future step, not designed here).

Components:
- `UploadPanel` — drag-and-drop / file-picker for PDFs, renders the accumulated file list with per-file status (`pending` / `processing` / `done` / `error`), and the "开始识别" button
- `Timeline` — renders entries with a non-null `date`, sorted ascending, alternating left/right around a center vertical line
- `UnreadableList` — renders entries with a null `date` as "该图片不可识别", grouped by source file

State is held in React component state only (`useState`/`useReducer`), scoped to the current browser session — refreshing the page clears everything. No backend persistence of files or results.

## 4. Backend Mock Endpoint

`POST /extract/mock/pdf`, added alongside the existing routes (new `src/api/mock_routes.py`, included into the same FastAPI app as `routes.py`).

- Request: single `UploadFile`. Validate `content_type == "application/pdf"`; reject otherwise with 400.
- Response: a fixed, hardcoded list of records (module-level constant — not randomized, not derived from the PDF's actual content). The fixed set includes both readable and unreadable entries so the frontend's timeline/unreadable-split logic has real data to exercise:

```python
class MockExtractedRecord(BaseModel):
    date: str | None            # ISO 8601, None if unreadable
    country: str | None
    direction: str | None       # "ENTRY" | "EXIT"
    raw_text: str | None
    confidence: float

class MockPdfExtractionResponse(BaseModel):
    source_file: str            # echoes the uploaded filename
    records: list[MockExtractedRecord]
```

Fixed fixture (illustrative — exact values are a free implementation choice as long as it includes at least one null-date entry):

```python
_FIXED_RECORDS = [
    MockExtractedRecord(date="2024-01-10", country="USA", direction="EXIT", raw_text="LAX 10 JAN 2024", confidence=0.92),
    MockExtractedRecord(date="2024-01-11", country="GBR", direction="ENTRY", raw_text="HEATHROW 11 JAN 2024", confidence=0.88),
    MockExtractedRecord(date="2024-02-20", country="GBR", direction="EXIT", raw_text="HEATHROW 20 FEB 2024", confidence=0.61),
    MockExtractedRecord(date=None, country=None, direction=None, raw_text=None, confidence=0.0),
]
```

No PDF parsing (no `pypdf`/page-count logic). Every valid PDF upload gets the same fixed response, tagged with its own filename in `source_file`. This is intentional: the endpoint's only job right now is to give the frontend a stable contract to build against.

## 5. Frontend Data Contract

```ts
interface TimelineEntry {
  id: string;                          // client-generated (uuid)
  sourceFile: string;                  // from MockPdfExtractionResponse.source_file
  date: string | null;
  country: string | null;
  direction: "ENTRY" | "EXIT" | null;
  rawText: string | null;
  confidence: number;
}
```

A pure function `partitionEntries(entries: TimelineEntry[]): { timeline: TimelineEntry[]; unreadable: TimelineEntry[] }`:
- `unreadable` = entries where `date === null`
- `timeline` = remaining entries, sorted by `date` ascending

This function is the one piece of non-trivial logic in the frontend and gets a unit test (see Testing).

## 6. Upload & Processing Flow

1. User adds one or more PDFs via drag-and-drop or file picker → each becomes a `pending` entry in the file list. Adding more files at any time appends to the list (accumulate, not replace).
2. Client-side validation on add: reject non-PDF files immediately (by MIME type/extension) with an inline message; they never reach `pending`.
3. User clicks "开始识别" → every `pending` (and any previously `error`) file is POSTed to `/api/extract/mock/pdf` (sequentially, to keep the flow simple and predictable). Each file's status flips to `processing`.
4. On success: status → `done`, and the returned `records` are converted to `TimelineEntry[]` (tagging `sourceFile`) and merged into the global entries list.
5. On failure (network/5xx): status → `error`, file stays in the list, is retryable by clicking "开始识别" again.
6. `done` files are never resent. The user can keep adding new files and repeat step 3 for just the new batch.

## 7. Error Handling

- Non-PDF file selected: rejected client-side before it's added to the list.
- Request failure: per-file `error` status, retryable, no global error modal.
- Mock endpoint itself has no failure modes beyond content-type validation (400) — it doesn't attempt real parsing, so there's nothing else to fail on.

## 8. Testing

- Backend: one test posting a dummy PDF (a minimal valid `%PDF-...` byte string is enough since content isn't parsed) to `/extract/mock/pdf`, asserting the response shape and that at least one record has `date: null`.
- Frontend: unit test for `partitionEntries` — covers the sort-by-date and null-date-goes-to-unreadable behavior. UI rendering is verified manually (dev server), no component-test framework setup required for this iteration.

## 9. Future Swap-In Point

When the real recognition module is ready, only `src/api/mock_routes.py`'s handler body changes (or the route is replaced by a call into the real detection+extraction pipeline already built in `src/ocr/` and `src/detection/`); the response schema (`MockPdfExtractionResponse`) and everything on the frontend stay the same, aside from possibly renaming the endpoint.
