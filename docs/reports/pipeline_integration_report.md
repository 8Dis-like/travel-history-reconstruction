# Sprint 1 Milestone Report: End-to-End Pipeline Integration

**Project:** Travel History Reconstruction from Travel Documents
**Team:** Hao Zhang · Zuyan Tao · Wilson Tee
**Report Date:** July 12, 2026
**Sprint:** 1 (June 22 – July 12, 2026)
**Status:** End-to-End Pipeline Operational (MVP)

---

## 1. Executive Summary

Sprint 1 aimed to complete **Stage 1 (Stamp Detection & Isolation)** and lay the groundwork for downstream extraction. By the end of the sprint, the team collaboratively delivered a working end-to-end prototype that spans preprocessing, detection, VLM-based extraction, and frontend visualization — reaching a functional proof-of-concept across Stages 1–3.

A user can now upload a passport page image (PNG, JPEG, or PDF) to the web frontend, and the system will detect stamp regions, attempt to extract date/country/direction fields via a cloud VLM, and render the results as an interactive travel timeline.

However, significant quality gaps remain — particularly on real-world scans — and the VLM provider and prompt strategy are still subject to optimization in Sprint 2.

### Sprint 1 Scorecard

| Objective | Status | Notes |
|---|---|---|
| Preprocessing pipeline functional | ✅ Done | Auto-orient, deskew, denoise, CLAHE — all operational |
| Stamp detection model trained | ✅ Done | YOLOv8 fine-tuned on Wilson's synthetic dataset |
| Synthetic dataset created & annotated | ✅ Done | 1,000 synthetic scenes generated and annotated (Wilson) |
| OCR/VLM extraction integrated | ✅ Done | Cloud VLM wired via factory pattern (Zuyan + Hao) |
| Frontend ↔ Backend connected | ✅ Done | React/AntD UI wired to live API (Zuyan + Hao) |
| Formal model evaluation metrics | 🟡 Pending | Validation script ready; formal run needed |

---

## 2. Work Completed by Member

### Hao Zhang — Preprocessing & Detection Pipeline
- Built the image enhancement pipeline (`enhancer.py`): auto-orientation via HoughLinesP analysis (90°/180°/270°), fine deskewing, CLAHE contrast enhancement, non-local means denoising
- Implemented the YOLOv8 stamp detection wrapper (`stamp_detector.py`) with structured output, crop extraction, and visualization
- Fine-tuned YOLOv8s on the synthetic dataset using Google Colab A100
- Integrated all pipeline stages into the FastAPI backend and wired the frontend to the live API
- Added multi-provider VLM support (factory pattern) and PDF ingestion via PyMuPDF

### Zuyan Tao — OCR/VLM & Frontend UI
- Designed and implemented the React/AntD frontend: file upload dropzone, timeline visualization, unreadable stamp handling
- Built the mock extraction endpoints that enabled parallel frontend development before the detector was ready
- Implemented the Claude VLM extractor module (`claude_extractor.py`) with structured JSON output
- Defined the API schema design (Pydantic models for stamp records, extraction fields, page responses)

### Wilson Tee — Data Engineering & Annotation
- Curated and sourced external stamp detection datasets from Roboflow Universe and Kaggle
- Generated the 1,000-image synthetic training dataset by overlaying stamp templates on passport page backgrounds
- Annotated bounding boxes in YOLO format for the entire synthetic dataset
- Collected and organized the team's raw passport scan samples (`data/raw/`)

---

## 3. Stamp Detection Model

### 3.1 Training Summary

| Parameter | Value |
|---|---|
| Base model | `yolov8s.pt` (COCO pretrained) |
| Training data | 1,000 synthetic passport scenes (Wilson) |
| Compute | Google Colab A100 |
| Epochs | 100 (early stopping, patience=20) |
| Output weights | `runs/best_stamp_model.pt` |

### 3.2 Validation

A held-out validation set of 1,000 synthetic scenes is at `data/synthetic_dataset/val`. Evaluation scripts are ready:

```bash
python scripts/verify_model.py
# or: yolo val model=runs/best_stamp_model.pt data=dataset.yaml
```

Formal metrics (mAP, Precision, Recall) have not yet been recorded and are a Sprint 2 priority.

### 3.3 Real-World Observations

We tested the pipeline on two categories of input and observed a notable domain gap:

**Synthetic images** (e.g., `scene_04000.jpg`):
- Detected 6 stamps with high confidence (85–98%)
- VLM extracted plausible countries and directions
- Some dates appeared to be misread or hallucinated by the VLM

**Raw passport scans** (e.g., `page_002.png`):
- Detected only ~2 of ~8 visible stamps
- Detected stamps were correctly localized
- VLM extraction on detected crops returned reasonable results

**Takeaway:** The model generalizes well within synthetic data but struggles with real scans. Bridging this gap — through real-data annotation and retraining — is the top priority going forward.

---

## 4. Pipeline Architecture (As-Built)

### 4.1 System Flow

```
Upload (PNG/JPG/PDF) → Preprocessing → YOLOv8 Detection → VLM Extraction → Timeline UI
                       (enhancer.py)   (stamp_detector)   (factory.py)     (React/AntD)
```

### 4.2 VLM Provider Architecture

The extraction layer uses a factory pattern (`src/ocr/factory.py`) supporting hot-swappable providers. The optimal VLM model and prompting strategy are still under evaluation:

| Provider | Vision | Cost | Current Status |
|---|---|---|---|
| Google Gemini | ✅ | Free tier available | Currently active for testing |
| Anthropic Claude | ✅ | ~$0.00025/stamp | Implemented, key needed |
| Local VLM        | ✅      | Free (GPU required) | Not yet tested               |

Switching providers requires only a `.env` change — no code modifications. The team will evaluate and compare providers in Sprint 2 to determine the best accuracy/cost tradeoff.

### 4.3 Key Technical Decisions

| Decision | Rationale |
|---|---|
| Python 3.11 dedicated Conda environment | Pydantic type syntax (`str \| None`) requires ≥3.10; isolates from system Python |
| PyMuPDF for PDF support | Rasterizes PDF pages at 300 DPI; lightweight, no system deps |
| Factory pattern for VLM providers | Enables rapid A/B testing of different models without touching pipeline code |
| Graceful degradation on missing API keys | Server stays up; returns empty fields instead of crashing |

---

## 5. Bug Fixes & Integration Work

| Issue | File | Fix |
|---|---|---|
| OpenCV `hForColorComponents` crash | `enhancer.py` | Mapped to correct keyword `hColor` |
| Hardcoded model path ignored argument | `stamp_detector.py` | Restored dynamic `model_path` resolution |
| HoughLinesP unpacking crash (numpy int32) | `enhancer.py` | Reshaped output to `(-1, 4)` |
| Pydantic crash on Python 3.9 | Environment | Migrated to Python 3.11 Conda env |
| Frontend rejected non-PDF uploads | `UploadPanel.tsx`, `App.tsx` | Expanded accept filter to PNG/JPEG/PDF |
| Frontend hit mock endpoint | `api.ts` | Rewired to live `/extract/page` |
| Missing API key crashed server | `claude_extractor.py` | Graceful degradation |

---

## 6. Environment Setup (For Teammates)

```bash
# 1. Create environment
conda create -n securiport python=3.11 -y && conda activate securiport

# 2. Install dependencies
pip install -r requirements.txt
pip install openai google-generativeai pymupdf

# 3. Configure .env (project root)
#   OCR_PROVIDER=gemini
#   GEMINI_API_KEY=your_key_from_aistudio.google.com

# 4. Run backend
uvicorn src.api.main:app --reload

# 5. Run frontend (separate terminal)
cd frontend && npm install && npm run dev
```

---

## 7. Known Gaps & Open Questions

| Area | Gap | Severity |
|---|---|---|
| Detection | Low recall on real passport scans (~25%) | 🔴 High |
| Detection | Overlapping stamps not separated | 🟡 Medium |
| VLM | Date hallucination on unclear stamps | 🟡 Medium |
| VLM | Optimal model/provider not yet determined | 🟡 Medium |
| Frontend | No stamp crop visualization | 🟡 Medium |
| Frontend | No export functionality (CSV/Sheets) | 🟡 Medium |
| Data | Limited real-world annotated data | 🔴 High |

---

## 8. File Reference

| Path | Description |
|---|---|
| `runs/best_stamp_model.pt` | Fine-tuned YOLOv8 weights |
| `src/preprocessing/enhancer.py` | Image enhancement pipeline |
| `src/detection/stamp_detector.py` | YOLOv8 inference wrapper |
| `src/ocr/factory.py` | VLM provider factory |
| `src/api/routes.py` | FastAPI endpoints |
| `frontend/src/api.ts` | Frontend API client |
| `scripts/verify_model.py` | Model evaluation script |
| `scripts/test_integration.py` | CLI integration test |

---

*Report prepared by Hao Zhang on behalf of the team.*
*Repository: [travel-history-reconstruction](https://github.com/8Dis-like/travel-history-reconstruction)*
