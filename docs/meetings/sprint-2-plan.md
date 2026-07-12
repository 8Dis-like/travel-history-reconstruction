# Sprint 2 Kickoff — July 13, 2026

**Sprint Duration:** July 13 – July 27, 2026 (2 weeks)
**Sprint Goal:** Close the real-world detection gap and harden the extraction pipeline for demo-quality results.

---

## 🎯 Sprint Objective

Sprint 1 delivered a working end-to-end prototype. Sprint 2 pivots from *"does it work?"* to *"does it work well on real data?"*

The model currently detects **6/6 stamps on synthetic images** but only **2/8 on real scans**. Closing this domain gap is the singular top priority. Secondary goals include hardening the VLM extraction (date validation, error handling) and expanding the frontend with visualization and export features.

---

## 📋 Sprint Backlog

### 🔴 P0 — Must Complete

| Task | Owner | Due | Acceptance Criteria |
|---|---|---|---|
| Run formal model validation on synthetic val set | Hao | Jul 14 | mAP@50, mAP@50-95, Precision, Recall recorded |
| Annotate ≥50 real passport pages (YOLO `.txt` format) | Wilson | Jul 17 | Annotations committed to `data/annotations/` |
| Retrain YOLOv8 on mixed real + synthetic dataset | Hao | Jul 20 | mAP@50 ≥ 0.70 on real test set |
| Add `python-dateutil` post-validation to VLM output | Zuyan | Jul 17 | Invalid dates rejected; ISO 8601 enforced |
| Everyone sets up `securiport` conda env locally | All | Jul 14 | `uvicorn` + `npm run dev` runs without errors |

### 🟡 P1 — Should Complete

| Task | Owner | Due | Acceptance Criteria |
|---|---|---|---|
| Add stamp crop gallery to frontend | Wilson | Jul 20 | Detected crops displayed with bounding boxes |
| Implement Gemini request batching with backoff | Zuyan | Jul 20 | Handles 15 RPM limit gracefully |
| Evaluate Claude Haiku as backup VLM provider | Zuyan | Jul 20 | Comparison table: accuracy vs. cost vs. speed |
| Experiment with 1280px inference for small stamps | Hao | Jul 24 | Recall comparison: 640px vs. 1280px |

### 🟢 P2 — Nice to Have

| Task | Owner | Due | Acceptance Criteria |
|---|---|---|---|
| Implement CSV export from frontend | Wilson | Jul 24 | Download button produces valid CSV |
| Implement Google Sheets push (per proposal §7.3) | Wilson | Jul 27 | One-click export to shared spreadsheet |
| Remove/rewire broken "Load demo data" button | Zuyan | Jul 17 | No broken UI elements |
| Add overlap-aware augmentation to training pipeline | Hao | Jul 27 | Training data includes synthetic overlaps |

---

## 🔗 Dependency Chain

```
Wilson annotates real data (Jul 17)
        ↓
Hao retrains detector (Jul 20)
        ↓
Zuyan tunes VLM prompts on new crops (Jul 22)
        ↓
End-to-end quality validated (Jul 24)
        ↓
Sprint 2 demo to team (Jul 27)
```

**Critical path:** Wilson's annotations are the blocker. If delayed, retraining and downstream tuning slip proportionally.

---

## 📊 Success Metrics

| Metric | Sprint 1 Baseline | Sprint 2 Target |
|---|---|---|
| Stamps detected on real scans (page_002.png) | 2/8 (25%) | ≥ 6/8 (75%) |
| Stamps detected on synthetic val | ~6/6 (100%) | Maintain ≥ 95% |
| Date extraction accuracy | Unknown (no ground truth) | ≥ 80% on English stamps |
| mAP@50 on real test set | Not measured | ≥ 0.70 |
| End-to-end processing time per page | ~15s (estimate) | Measure and establish baseline |

---

## 👥 Role Focus

| Member | Sprint 1 Focus | Sprint 2 Pivot |
|---|---|---|
| **Hao Zhang** | Pipeline architecture, synthetic training, integration | Real-data retraining, model evaluation, preprocessing tuning |
| **Zuyan Tao** | Mock endpoints, AntD UI scaffold, OCR module structure | VLM hardening, date validation, error handling, provider eval |
| **Wilson Tee** | Data collection, external dataset sourcing | Real-data annotation (critical path), frontend features, export |

---

## 🗓️ Key Dates

| Date | Event |
|---|---|
| **Jul 13** | Sprint 2 kickoff meeting (this document) |
| **Jul 14** | Formal model eval completed; all envs verified |
| **Jul 17** | First annotation batch (≥50 pages) due; date validation merged |
| **Jul 20** | Retrained model available; stamp gallery in frontend |
| **Jul 24** | End-to-end quality checkpoint |
| **Jul 27** | Sprint 2 review & demo |

---

## 📝 Notes

- **Environment:** Python 3.11 via Conda (`securiport` env) is now mandatory. The old base/Anaconda env crashes due to Pydantic type syntax incompatibilities.
- **API Key:** Currently using Google Gemini 3.5 Flash (free, 15 RPM). Key is stored in `.env` (gitignored). Each team member needs their own key from [Google AI Studio](https://aistudio.google.com/app/apikey).
- **Large files:** Model weights (`*.pt`) and datasets remain gitignored. Share via the [team Google Drive](https://drive.google.com/drive/u/0/folders/1SiDs1cU4OYypSrmM5DO1fU8h_ET58ff7).
- **Meetings:** Weekly standup (Monday, 15 min) + bi-weekly sponsor check-in with Alvaro.
