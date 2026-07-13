**Project:** Travel History Reconstruction from Travel Documents
**Meeting Type:** Sprint 2 Kickoff & Direction Sync
**Duration:** 30 min (+ open discussion as needed)
**Date/Time:** 7 p.m. PST, July 13, 2026

---

## 1. Sprint 1 Recap (5 min) — Hao

What we shipped as a team:

- **Wilson:** Generated and annotated 1,000 synthetic passport scenes for detection training; curated external datasets from Roboflow Universe and Kaggle
- **Zuyan:** Built the React/AntD frontend (upload, timeline, unreadable handling); implemented Claude VLM extractor and mock endpoints for parallel development
- **Hao:** Built preprocessing pipeline (auto-orient, deskew, denoise, CLAHE); fine-tuned YOLOv8 on Colab A100; integrated all stages into FastAPI backend

**Where we landed:**
- End-to-end prototype works: upload image → detect stamps → VLM extraction → timeline display
- Model works well on synthetic data (~6/6 stamps detected) but struggles on real scans (~2/8)
- VLM provider and prompting strategy still under evaluation — current setup works but accuracy needs improvement

---

## 2. The Road Ahead (10 min) — All

### Updated Stage Map

Based on Sprint 1 experience, stages 2–4 from the original proposal naturally blend together in practice. Proposed simplification:

| Stage | Goal | Status |
|---|---|---|
| **Stage 1** — Stamp Detection & Isolation | Detect all stamp regions, output crops | ✅ MVP Done |
| **Stage 2-3-4** — Extraction & Timeline | Extract fields (date, country, direction) + reconstruct chronological timeline | 🟡 In Progress |
| **Stage 5** — Multilingual & Production | Non-English support, hardening | ⬜ Not Started |

The combined stage reflects reality: once detection crops exist, extraction, validation, and timeline assembly are tightly interleaved — not sequential. We should work on them as one continuous effort.

### Proposed Work Split (System Responsibility)

Rather than splitting by pipeline stage, split by **system concern** to minimize cross-dependencies:

| Member | Responsibility | Scope |
|---|---|---|
| **Hao (Zagho)** | Quality Assurance | Model evaluation & benchmarking; detection retraining on real data; VLM model selection & prompt optimization |
| **Zuyan** | Core Function | Timeline reconstruction data structures; chronological ordering logic; entry-exit pairing; conflict resolution |
| **Wilson** | Appearance & Completeness | Frontend feature completeness (stamp gallery, export, data quality dashboard); end-user experience |

**Discussion:** Does this split feel right to everyone? Any concerns about scope or overlap?

---

## 3. Data Discussion (Open) — All

We need more data to bridge the real-world detection gap. Topics to discuss:

- **From Alvaro:** Can Securiport provide additional passport scan samples? What format? Any restrictions?
- **Annotation effort:** How many real pages can we realistically annotate in Sprint 2? What tool works best?
- **Data diversity:** Do we need stamps from specific regions/languages to be representative?
- **Ground truth for VLM:** Should we build a small manually-labeled extraction ground truth set to benchmark VLM accuracy?

> This is an open discussion — take as much time as needed. Data quality directly determines our Sprint 2 outcomes.

---

## 4. Sprint 2 Logistics (5 min) — Hao

### Reminders
- **Environment:** Everyone must use the `securiport` Conda env (Python 3.11). Verify you can run both backend and frontend locally.
- **Git:** Feature branches → PR → review → merge. No direct pushes to `master`.
- **Large files:** Weights and datasets stay gitignored. Share via Google Drive.
- **VLM keys:** Each person gets their own free API key from [Google AI Studio](https://aistudio.google.com/app/apikey). Key goes in `.env` (gitignored).

### Sprint 2 Cadence
- Weekly standup (Monday, 15 min)
- Bi-weekly sponsor check-in with Alvaro
- Sprint 2 review: ~July 27

---

## 5. Action Items (5 min) — Hao

| # | Action Item | Owner | Due |
|---|---|---|---|
| 1 | Run formal model validation, record mAP/Precision/Recall | Hao | July 15 |
| 2 | Reach out to Alvaro re: additional data | Hao | July 15 |
| 3 | Draft timeline reconstruction data structures | Zuyan | July 18 |
| 4 | Begin annotating real passport pages | Wilson + All | Ongoing |
| 5 | Evaluate 2–3 VLM providers for accuracy comparison | Hao | July 20 |
| 6 | Everyone: verify `securiport` env runs locally | All | Before next standup |

---

## Pre-Read Materials

1. 📊 [Sprint 1 Milestone Report](../reports/pipeline_integration_report.md) — what we built, what works, what doesn't
2. 📄 [Project Proposal](../proposal.md) — Section 3 (Staged Milestones), Section 9 (Timeline)
3. 🔗 [Notion Sprint Board](https://app.notion.com/p/21fd6700a92f4077908ca14f64435908)
