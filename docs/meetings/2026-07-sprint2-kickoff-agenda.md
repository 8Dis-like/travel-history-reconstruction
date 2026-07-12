**Project:** Travel History Reconstruction from Travel Documents
**Meeting Type:** Sprint 2 Kickoff & Pivot Sync
**Duration:** 30 min
**Date/Time:** 7 p.m. PST, July 13, 2026

---

## 1. Sprint 1 Recap & Demo (5 min) — Hao

Quick demo of what we shipped in Sprint 1:

- ✅ **Preprocessing pipeline** production-ready: auto-orientation (90°/180°/270°), deskewing, CLAHE contrast, NLM denoising
- ✅ **YOLOv8 stamp detector** fine-tuned on 1,000 synthetic scenes (Colab A100), weights at `runs/best_stamp_model.pt`
- ✅ **VLM extraction** integrated via Google Gemini 3.5 Flash (free tier, 15 RPM) — extracts date, country, direction as structured JSON
- ✅ **Full-stack wiring** complete: React/AntD frontend → FastAPI backend → live pipeline → interactive timeline
- ✅ **Multi-format support**: PNG, JPEG, and PDF uploads all functional

**Live demo:** Upload `data/raw/page_002.png` and `synthetic_dataset/val/scene_04000.jpg` → show detection + timeline output side-by-side.

**Key finding from Sprint 1:**
The model detects **6/6 stamps on synthetic images** but only **2/8 on real scans**. This domain gap is the #1 priority for Sprint 2.

---

## 2. Gap Analysis & Pivot Discussion (10 min) — All

### The Problem

Our detector was trained exclusively on synthetic data. Real passport scans differ in:
- Background texture (paper grain, scanner artifacts)
- Ink quality (faded, smudged, partially stamped)
- Stamp overlap (multiple stamps sharing the same region)
- Rotation and scale variation

### Proposed Pivot: Real-Data-First Strategy

| Priority | Gap | Sprint 2 Fix | Owner |
|---|---|---|---|
| 🔴 P0 | Detection misses on real scans | Annotate 50+ real pages → retrain YOLOv8 | Wilson + Hao |
| 🔴 P0 | No formal model evaluation metrics | Run `verify_model.py`, record mAP/Precision/Recall | Hao |
| 🟡 P1 | VLM date hallucination | Add `python-dateutil` validation + confidence thresholds | Zuyan |
| 🟡 P1 | No stamp gallery in frontend | Add cropped stamp visualization with bounding boxes | Wilson |
| 🟡 P1 | Gemini rate limit (15 RPM) | Implement request batching with exponential backoff | Zuyan |
| 🟢 P2 | No export (CSV/Google Sheets) | Implement export per proposal spec (Section 7.3) | Wilson |
| 🟢 P2 | "Load demo data" button broken | Remove or rewire to a real sample image | Zuyan |

**Discussion questions:**
1. Wilson — How many of the 38 raw pages have you annotated so far? What tool are you using (Roboflow/CVAT)?
2. Zuyan — Should we evaluate Claude Haiku as a backup VLM? It has better accuracy but costs ~$0.00025/stamp.
3. All — Should we target 1280px inference for small stamp detection, or stick with 640px for speed?

---

## 3. Sprint 2 Role Assignments (5 min) — All

Review and confirm updated responsibilities for the next two weeks:

| Member | Primary Focus | Sprint 2 Deliverables |
|---|---|---|
| **Hao Zhang** | Detection Quality | Retrain YOLOv8 on real+synthetic mix; run formal eval; optimize preprocessing for real scans |
| **Zuyan Tao** | VLM & Backend Hardening | Add date validation; implement retry/backoff for Gemini; evaluate Claude as fallback |
| **Wilson Tee** | Data & Frontend | Annotate ≥50 real pages; add stamp gallery view; implement CSV export |

**Critical dependency chain:**
```
Wilson's annotations → Hao's retraining → Zuyan's VLM tuning → End-to-end quality
```

Wilson's annotations are on the critical path — we need them by **July 17** to unblock retraining.

---

## 4. Workflow & Standards Check (5 min) — All

### Git Workflow Reminder
- **Branching:** Feature branches off `master` → PR → ≥1 review → merge
- **Naming:** `feat/real-data-retrain`, `feat/stamp-gallery`, `fix/date-validation`
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`, `test:`)
- **Large files:** Model weights and datasets stay in `.gitignore` — share via Google Drive

### Environment Setup (New!)
Sprint 1 revealed that a **dedicated Conda environment** is required:
```bash
conda create -n securiport python=3.11 -y && conda activate securiport
pip install -r requirements.txt && pip install openai google-generativeai pymupdf
```
Everyone must verify they can run the backend (`uvicorn src.api.main:app --reload`) and frontend (`cd frontend && npm run dev`) before next standup.

### Notion Updates
- Move Sprint 1 cards to **Done** column
- Create Sprint 2 task cards per the deliverables above
- Update the [Sprint 1 Milestone Report](../reports/pipeline_integration_report.md) with formal eval metrics once available

---

## 5. Action Items & Next Steps (5 min) — Hao

| # | Action Item | Owner | Due |
|---|---|---|---|
| 1 | Run formal model validation (`verify_model.py`), record mAP metrics | Hao | July 14 |
| 2 | Annotate first batch of 20 real passport pages (YOLO format) | Wilson | July 17 |
| 3 | Add `python-dateutil` post-validation to Gemini extractor output | Zuyan | July 17 |
| 4 | Retrain YOLOv8 on mixed real+synthetic dataset (Colab A100) | Hao | July 20 |
| 5 | Add stamp crop gallery view to frontend | Wilson | July 20 |
| 6 | Evaluate Claude Haiku as backup VLM provider | Zuyan | July 20 |
| 7 | Implement CSV/Google Sheets export | Wilson | July 24 |
| 8 | Everyone: verify local environment runs (`securiport` conda env) | All | Before next standup |

---

## Pre-Read Materials

Please review these before the meeting:

1. 📊 [Sprint 1 Milestone Report](../reports/pipeline_integration_report.md) — full technical status, gap analysis, and Sprint 2 priorities
2. 📄 [Project Proposal](../proposal.md) — especially Section 3 (Staged Milestones) and Section 9 (Timeline)
3. 🔗 [Notion Sprint Board](https://app.notion.com/p/21fd6700a92f4077908ca14f64435908) — current task status
