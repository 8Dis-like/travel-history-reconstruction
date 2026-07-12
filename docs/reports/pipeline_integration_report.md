# Sprint 1 Milestone Report: End-to-End Pipeline Integration

**Project:** Travel History Reconstruction from Travel Documents
**Team:** Hao Zhang · Zuyan Tao · Wilson Tee
**Report Date:** July 12, 2026
**Sprint:** 1 (June 22 – July 12, 2026)
**Status:** ✅ End-to-End Pipeline Operational

---

## 1. Executive Summary

Sprint 1 set out to complete **Stage 1 (Stamp Detection & Isolation)** and make meaningful progress toward **Stage 3 (Full Field Extraction via VLM)**. As of this report, we have exceeded Stage 1 and achieved a working end-to-end prototype that spans detection through structured OCR output — effectively reaching a functional **Stage 3 MVP**.

**Key Achievement:** A user can now upload a passport page image (PNG, JPEG, or PDF) to our web frontend, and the system will automatically detect stamp regions, extract date/country/direction fields via a cloud Vision-Language Model, and render the results as an interactive travel timeline — all in a single click.

### Sprint 1 Scorecard

| Objective | Target | Actual | Status |
|---|---|---|---|
| Stamp detection model trained & validated | mAP@50 ≥ 0.70 | **TBD** (synthetic val pending) | 🟡 Model trained, formal eval needed |
| Preprocessing pipeline functional | Auto-orient, deskew, denoise, CLAHE | All 4 stages operational | ✅ Complete |
| OCR/VLM extraction integrated | At least 1 provider working | Gemini 3.5 Flash (free tier) | ✅ Complete |
| Frontend ↔ Backend connected | Upload → results displayed | Fully wired via Vite proxy | ✅ Complete |
| API server deployable locally | `uvicorn` starts without errors | Python 3.11 env, all deps resolved | ✅ Complete |

---

## 2. Stamp Detection Model

### 2.1 Training Summary

| Parameter | Value |
|---|---|
| Base model | `yolov8s.pt` (COCO pretrained) |
| Training data | 1,000 synthetic passport scenes (generated via stamp overlay augmentation) |
| Compute | Google Colab A100 (40 GB VRAM) |
| Epochs | 100 (early stopping with patience=20) |
| Image size | 640×640 |
| Output weights | `runs/best_stamp_model.pt` |

### 2.2 Validation Design

A held-out validation set of **1,000 synthetic scenes** is available at `data/synthetic_dataset/val`. The evaluation pipeline is implemented in two ways:

```bash
# Option A: Dedicated script
python scripts/verify_model.py

# Option B: YOLO CLI
yolo val model=runs/best_stamp_model.pt data=dataset.yaml
```

**Expected metric thresholds** (based on synthetic data characteristics):

| Metric | Target | Rationale |
|---|---|---|
| mAP@50 | ≥ 0.95 | Synthetic stamps have clean borders |
| mAP@50-95 | ≥ 0.85 | Tight bounding box regression |
| Recall | ≥ 0.90 | Must catch all stamps for downstream OCR |

**Artifacts generated** by the validation pipeline:
- `runs/detect/val/confusion_matrix.png`
- `runs/detect/val/PR_curve.png`
- `runs/detect/val/val_batch*.jpg` (prediction overlays)

> **⚠️ Action Required:** The formal validation run has not yet been executed on the team's local machines. This is the first task for Sprint 2 kickoff — run the evaluation, record the exact metrics, and update this section.

### 2.3 Real-World Performance Observations

We tested the pipeline on two categories of input:

**A. Raw passport scans** (`data/raw/page_002.png`):
- The model detected **2 out of ~8 visible stamps**
- Detected stamps were correctly localized with high confidence
- Gemini VLM successfully extracted: `USA · ENTRY · 1997-06-09 (95%)` and `ARG · ENTRY · 1997-10-07 (95%)`
- **Gap:** Many stamps were missed — likely due to domain shift between synthetic training data and real scanned documents (different backgrounds, ink fading, overlapping stamps)

**B. Synthetic validation images** (`synthetic_dataset/val/scene_04000.jpg`):
- The model detected **6 stamps** with high confidence (85-98%)
- Gemini VLM correctly extracted countries (TTO, MLT, ZAF, RUS, LBN, PAN) and directions
- **Gap:** Some dates were hallucinated or incorrectly read (e.g., misreading "17 MAR 2019" as "2024-03-17")

**Key Insight:** The model generalizes well on synthetic data but struggles with real-world scans. This confirms that **real-data fine-tuning is the critical next step**.

---

## 3. Pipeline Architecture (As-Built)

### 3.1 System Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│ Upload File  │────▶│ Preprocessing│────▶│  Detection   │────▶│  VLM / OCR   │────▶│  Timeline   │
│ (PNG/JPG/PDF)│     │ (enhancer.py)│     │  (YOLOv8)    │     │  (Gemini)    │     │  (Frontend) │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └────────────┘
                     Auto-orient          Bounding boxes       Structured JSON      Interactive
                     Deskew + CLAHE       + Crop extraction    per stamp            timeline UI
                     Denoise (NLM)        best_stamp_model.pt  date/country/dir     + confidence
```

### 3.2 Technology Stack (Implemented)

| Layer | Technology | Status |
|---|---|---|
| **Frontend** | React 18 + Ant Design 5 + Vite | ✅ Operational |
| **Backend API** | FastAPI + Uvicorn | ✅ Operational |
| **Preprocessing** | OpenCV (CLAHE, NLM denoise, HoughLinesP deskew) | ✅ Operational |
| **Detection** | YOLOv8s (Ultralytics) + fine-tuned weights | ✅ Operational |
| **OCR / VLM** | Google Gemini 3.5 Flash (free tier, 15 RPM) | ✅ Operational |
| **Environment** | Python 3.11 (Conda: `securiport`) | ✅ Configured |

### 3.3 OCR Provider Architecture

The extraction layer uses a **factory pattern** (`src/ocr/factory.py`) that supports hot-swapping between providers:

| Provider | Config Value | Vision Support | Cost | Status |
|---|---|---|---|---|
| **Gemini** | `OCR_PROVIDER=gemini` | ✅ Native | Free (15 RPM) | ✅ Active |
| Claude | `OCR_PROVIDER=claude` | ✅ Native | ~$0.00025/stamp | ⬜ Key needed |
| DeepSeek | `OCR_PROVIDER=deepseek` | ❌ Text only | Cheap | ❌ Incompatible |
| Local VLM | `OCR_PROVIDER=local` | ✅ Native | Free (GPU req) | ⬜ Not tested |

Switching providers requires only a `.env` change + server restart — no code modifications.

---

## 4. Integration Work Completed

### 4.1 Git Synchronization
- Merged Zuyan's AntD frontend UI revamp and mock extraction endpoints from `master`
- Resolved merge conflicts between preprocessing and API route modules

### 4.2 Bug Fixes & Refactoring

| Issue | File | Fix |
|---|---|---|
| OpenCV `hForColorComponents` crash | `enhancer.py` | Mapped to correct Python keyword `hColor` |
| Hardcoded model path ignored `model_path` arg | `stamp_detector.py` | Restored dynamic path resolution |
| `line[0]` unpacking crash (numpy int32) | `enhancer.py` | Reshaped HoughLinesP output to `(-1, 4)` |
| Pydantic `str | None` syntax crash on Python 3.9 | `mock_routes.py` | Migrated to Python 3.11 environment |
| Frontend rejected non-PDF uploads | `App.tsx`, `UploadPanel.tsx` | Expanded accept filter to PNG/JPEG/PDF |
| Frontend hit mock endpoint instead of live API | `api.ts` | Rewired to `/api/extract/page` via Vite proxy |
| Missing API key crashed entire server | `claude_extractor.py` | Added graceful degradation (return `None`) |

### 4.3 New Modules Created

| Module | Purpose |
|---|---|
| `src/ocr/deepseek_extractor.py` | DeepSeek API integration (text-only — unsuitable for our use case) |
| `src/ocr/gemini_extractor.py` | Google Gemini 3.5 Flash VLM integration (currently active) |
| `scripts/test_integration.py` | End-to-end pipeline sanity check (CLI, no frontend needed) |

### 4.4 PDF Support
- Installed **PyMuPDF** (`pymupdf`) for native PDF parsing
- Backend now rasterizes each PDF page at 300 DPI and processes every page through the full detection → OCR pipeline
- Frontend dropzone accepts `application/pdf`, `image/png`, and `image/jpeg`

---

## 5. Environment Setup (Reproducibility)

For any team member to run the full system locally:

```bash
# 1. Create the conda environment
conda create -n securiport python=3.11 -y
conda activate securiport

# 2. Install dependencies
pip install -r requirements.txt
pip install openai google-generativeai pymupdf

# 3. Configure API credentials
# Create .env in project root:
#   GEMINI_API_KEY=your_key_here
#   OCR_PROVIDER=gemini

# 4. Start the backend
uvicorn src.api.main:app --reload

# 5. Start the frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Navigate to `http://localhost:5173` and upload a passport image.

---

## 6. Gap Analysis & Sprint 2 Priorities

### 6.1 Detection Gaps

| Gap | Severity | Root Cause | Proposed Fix |
|---|---|---|---|
| Misses stamps on real scans | 🔴 High | Model trained only on synthetic data | Fine-tune on Wilson's annotated real data |
| Overlapping stamps not separated | 🟡 Medium | No overlap-aware augmentation | Add overlap augmentation to training pipeline |
| Small/faded stamps missed | 🟡 Medium | Training at 640px may lose detail | Experiment with 1280px input + multi-scale inference |

### 6.2 OCR/VLM Gaps

| Gap | Severity | Root Cause | Proposed Fix |
|---|---|---|---|
| Date hallucination on unclear stamps | 🟡 Medium | VLM fills in blanks creatively | Add confidence thresholds; reject low-confidence dates |
| Gemini rate limit (15 RPM) | 🟡 Medium | Free tier constraint | Batch processing with backoff; or switch to Claude for bulk |
| No date format validation | 🟢 Low | Raw VLM output accepted as-is | Add `python-dateutil` post-processing to validate ISO dates |

### 6.3 Frontend Gaps

| Gap | Severity | Root Cause | Proposed Fix |
|---|---|---|---|
| "Load demo data" button broken | 🟢 Low | Still hits deprecated mock endpoint | Remove or rewire to a real sample image |
| No stamp crop visualization | 🟡 Medium | Frontend only shows text fields | Add a stamp gallery view with bounding box overlays |
| No export functionality | 🟡 Medium | Not yet implemented | Add CSV/Google Sheets export per proposal spec |

---

## 7. File Reference

| Path | Description |
|---|---|
| `runs/best_stamp_model.pt` | Fine-tuned YOLOv8 weights (synthetic data) |
| `src/preprocessing/enhancer.py` | Image enhancement pipeline |
| `src/detection/stamp_detector.py` | YOLOv8 inference wrapper |
| `src/ocr/gemini_extractor.py` | Active VLM extractor (Gemini 3.5 Flash) |
| `src/ocr/factory.py` | Provider factory (gemini / claude / deepseek / local) |
| `src/api/routes.py` | FastAPI endpoints (`/extract/page`, `/extract/stamp`) |
| `src/api/main.py` | Application entry point |
| `frontend/src/api.ts` | Frontend API client (wired to live backend) |
| `scripts/test_integration.py` | CLI integration test |
| `scripts/verify_model.py` | Model evaluation script |
| `dataset.yaml` | YOLO dataset configuration |

---

## 8. Conclusion

Sprint 1 has delivered a **functional end-to-end prototype** that demonstrates the full vision of the project — from raw passport upload to structured travel timeline. While the detection model requires significant improvement on real-world data, the architectural foundation is solid: the preprocessing, detection, VLM extraction, API, and frontend layers are all operational and modularly designed for rapid iteration.

The team is well-positioned to pivot Sprint 2 toward **real-data quality** — annotating real passport scans, retraining the detector, and hardening the VLM extraction pipeline to produce production-grade results.

---

*Report prepared by Hao Zhang. For questions, refer to the [project repository](https://github.com/8Dis-like/travel-history-reconstruction) or the [Notion workspace](https://app.notion.com/p/21fd6700a92f4077908ca14f64435908).*
