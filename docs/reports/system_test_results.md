# Comprehensive System Test Results & Pipeline Report

**Date:** July 24, 2026  
**Project:** Travel History Reconstruction from Travel Documents  
**Status:** Sprint 2 Active

---

## 1. Executive Summary

The end-to-end travel history reconstruction system is currently operational on the `master` branch. 

**Sprint 1 vs Sprint 2 Overview:**
- **Sprint 1 (Legacy):** The pipeline was brittle. It relied on clean, perfectly upright crops, and it isolated stamp extraction without any temporal understanding or chronological sorting.
- **Sprint 2 (Current):** We have successfully transformed the system into a robust pipeline by introducing a **Multi-Rotation Strategy** (which dynamically handles any raw photo orientation), **Chronological Timeline Reconstruction** (ordering the extracted stamp data into a cohesive travel history), and a dynamic, **Config-driven VLM factory** allowing seamless swapping between models like Claude and Gemini.

---

## 2. Managing the VLM Model API

The VLM extraction layer (which currently uses Claude) is entirely configuration-driven to ensure API keys are secure and models can be swapped without altering code.

### 2.1 API Key Configuration (`.ENV`)
API keys must never be committed. They are securely injected via the `.ENV` file at the root of the project.
- Obtain your personal API key from [Google AI Studio](https://aistudio.google.com/app/apikey) (or Anthropic Console, etc.).
- Ensure your `.ENV` file contains the corresponding keys, for example:
  ```env
  GEMINI_API_KEY=your_gemini_api_key_here
  ANTHROPIC_API_KEY=your_anthropic_api_key_here
  OCR_PROVIDER=gemini
  ```
- The `.ENV` file is actively ignored by `.gitignore`.

### 2.2 Model Selection (`configs/pipeline.yaml`)
To change the active provider or model, edit the `ocr` section of `configs/pipeline.yaml`. No Python code needs to be modified.
```yaml
ocr:
  engine: "claude"            # Set to "claude", "gemini", etc.
  claude:
    model: "claude-3-5-sonnet-20240620"
    max_tokens: 256
```
The factory function `create_extractor_from_config()` automatically parses this file and instantiates the correct client.

---

## 3. Running the Pipeline Locally

Ensure your local Conda environment (`securiport`, Python 3.11) is activated.

### 3.1 Running the End-to-End Integration Test
To quickly test the pipeline (Enhancer -> Multi-Rotation YOLO Detection -> OCR Extraction) on sample raw images:
```bash
python scripts/test_integration.py
```
*Note: This script requires images in `data/raw/` and will output the extracted timeline elements to the console.*

### 3.2 Running the FastAPI Backend
To launch the API endpoints for the web frontend to consume:
```bash
uvicorn src.api.main:app --reload
```
- The server runs on `http://127.0.0.1:8000`.
- The main pipeline endpoint is located at `POST /extract/page` (accepts PDF, PNG, JPEG).

### 3.3 Running the React Frontend
The web interface is isolated in its own package. To run it, you must first navigate into the `frontend` directory:
```bash
cd frontend
npm install
npm run dev
```
*Note: Do not run `npm install` or `npm run dev` in the project root.*

---

## 4. Test Results and Validation

### 4.1 OCR Rotation Robustness (Benjamin's Eval)
**Methodology:** Tested 30 hand-labeled stamp crops across 7 angles [0, 20, 45, 75, 90, 180, 220].
**Result:** The Claude 3.5 Sonnet VLM is highly robust against rotated stamp crops. It maintained over a 95% accuracy rate for date, country, and direction extraction regardless of orientation. This confirmed the VLM was **not** the bottleneck.

### 4.2 Real-World Pipeline Bottleneck Diagnostics
**Methodology:** Evaluated un-oriented, raw passport pages.
**Result:**
- **Mode A (Current):** YOLOv8 completely failed to detect stamps (0 stamps found) when the raw passport page was rotated/upside down.
- **Mode B (Multi-Rotation Strategy):** By proactively forcing the raw image through 4 rotations (0, 90, 180, 270 degrees) and selecting the angle yielding the highest YOLO confidence, detection recall jumped from 0 to 100%.
**Status:** **RESOLVED.** This multi-rotation strategy has been successfully integrated into all main pipelines (`src/api/routes.py` and `scripts/test_integration.py`).

### 4.3 Timeline Reconstruction
**Methodology:** Benjamin's new chronological timeline logic evaluates synthetic scenes using the `src/reconstruction/scene_eval.py` tools.
**Result:** Integrated successfully into the `master` branch. The backend data structures successfully order the extracted VLM fields by date.

---

## 5. Branch Structure & Proposed Reorganization

### 5.1 Current Messy State
The remote repository currently contains several merged or abandoned branches:
- `master` (Up to date with all recent fixes)
- `synthetic-scenes` (Active/Merged)
- `timeline-reconstruction` (Merged into master/synthetic-scenes)
- `wilsontee` (Personal dev branch)
- `zuyantao` (Personal dev branch)

### 5.2 Next Steps for Repository Management
To keep the Git graph clean as the team collaborates:
1. **Delete Stale Branches:** `wilsontee` and `zuyantao` should be deleted from GitHub since their work has been merged into `master`.
2. **Adopt Feature Branching:** Use descriptive names for new work (e.g., `feat/multilingual-support`, `fix/fastapi-timeout`).
3. **Pull Request Workflow:** Always open a PR against `master`, ensuring code is reviewed before clicking "Squash and Merge" (which prevents thousands of small commits from cluttering the `master` graph).
4. **.gitignore Adherence:** Ensure all data, especially `/data/` and `__MACOSX/` directories, are strictly ignored to prevent large binary blobs from entering the version history.
