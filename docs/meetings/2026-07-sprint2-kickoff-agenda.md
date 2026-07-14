# Sprint 2 Kickoff & Direction Sync (Agenda & Minutes)

**Project:** Travel History Reconstruction from Travel Documents  
**Meeting Type:** Sprint Kickoff & Sync  
**Duration:** 30 min (Actual: extended for discussion)  
**Date/Time:** 7 p.m. PST, July 13, 2026  
**Participants:** Hao Zhang (Zagho), Zuyan Tao (Benjamin), Wilson Tee  

---

## 1. Meeting Summary & Minutes (Zoom AI Recap)

### 1.1 Executive Summary
Hao led the kickoff meeting for the second stage of the project, reviewing the completed work from Stage 1 (generating synthetic passport scenes, building the React frontend, and implementing the preprocessing pipeline with YOLOv8 model integration). Hao demonstrated the end-to-end prototype (image upload, stamp detection, VLM extraction, and timeline display). The prototype runs well on synthetic data but struggles with real-world raw images. The team discussed the current pipeline and identified a critical need to pinpoint which specific components are causing reliability issues on real data. 

### 1.2 Data Structure & Testing Discussion
- **Data Structure:** Benjamin and Hao discussed the data structure requirements for the timeline. Hao suggested using a simple linked list approach to order the travel events.
- **Frontend Integration:** Wilson was assigned to handle the frontend appearance design, focusing on making it feel production-ready, and will coordinate closely with Benjamin for backend integration.
- **Testing Status:** Hao presented the fine-tuning results based on synthetic data (including the confusion matrix), but noted that testing on real passport data is incomplete, making the real-world results unreliable at this stage.

### 1.3 Pipeline Reliability & Image Rotations
- **Bottleneck Search:** The team discussed reliability issues in the stamp detection and VLM extraction chain. Wilson suggested testing the YOLO model directly on raw images from Alvaro to isolate whether the failures stem from detection or VLM extraction.
- **Rotation Handling:** Benjamin noted that incorrectly rotated images negatively impact VLM extraction performance.
- **Multi-Rotation Testing:** Hao explained that the current image processing pipeline performs boundary cutting, rotation, and YOLO detection before passing data to Benjamin's VLM module without writing intermediate data to disk. To improve detection/extraction accuracy, Benjamin suggested testing four different rotated versions of the images (0, 90, 180, and 270 degrees). Wilson suggested starting with a subset of two rotations and scaling up to four if needed. The team agreed to implement a testing method to pinpoint this bottleneck.

### 1.4 Model Performance & Project Updates
- **VLM Models:** Benjamin discussed the potential of using Claude 3.5 Sonnet and Claude 3.5 Haiku, noting that higher-tier models perform better and reduce text extraction discrepancies.
- **Debugging Branch:** Hao suggested creating a dedicated Git branch to isolate and pinpoint these quality/integration issues.
- **Communication & Schedule:** Hao proposed communicating in Chinese via WeChat for daily convenience. The team confirmed their next meeting for **Thursday at 6 PM** to follow up on these points. The team acknowledged the successful completion of Sprint 1, with plans to officially kick off Sprint 2 execution heading into August.

---

## 2. Updated Stage Map & Road Ahead

Based on Sprint 1 testing, Stages 2, 3, and 4 from our original proposal naturally merge in practice since extraction, validation, and timeline assembly are tightly coupled. 

| Stage | Goal | Status |
|---|---|---|
| **Stage 1** — Stamp Detection & Isolation | Detect all stamp regions, output crops | ✅ MVP Done |
| **Stage 2-3-4** — Extraction & Timeline | Extract fields (date, country, direction) + reconstruct chronological timeline | 🟡 In Progress |
| **Stage 5** — Multilingual & Production | Non-English support, system hardening | ⬜ Not Started |

---

## 3. Work Split (System Responsibility)

To minimize mutual dependencies, responsibilities are split by system concerns:

*   **Hao Zhang (Zagho) — Quality Assurance (QA):**
    *   Pinpointing pipeline quality and reliability bottlenecks.
    *   Model testing, fine-tuning, and evaluation.
    *   VLM model selection and prompt optimization.
*   **Zuyan Tao (Benjamin) — Core Function:**
    *   Backend data structures (e.g., linked list for travel history).
    *   Core timeline reconstruction logic.
    *   VLM extraction integration.
*   **Wilson Tee — Appearance & Completeness:**
    *   Frontend design, completeness, and user experience.
    *   Timeline presentation and stamp visualization.
    *   Coordinating with Benjamin for API integration.

---

## 4. Sprint 2 Logistics & Reminders

- **Environment:** Everyone must use the `securiport` Conda env (Python 3.11). Verify you can run both backend and frontend locally.
- **Git:** Feature branches → PR → review → merge. No direct pushes to `master`.
- **Large files:** Weights and datasets stay gitignored. Share via Google Drive.
- **VLM keys:** (For your information) Each person gets their own free API key from [Google AI Studio](https://aistudio.google.com/app/apikey). Key goes in `.env` (gitignored).

### Sprint 2 Cadence
- Weekly standup (Monday, 15 min)
- Bi-weekly sponsor check-in with Alvaro
- Sprint 2 review: ~July 27

---

## 5. Action Items & Next Steps

| # | Action Item | Owner | Due |
|---|---|---|---|
| 1 | Redo evaluations to pinpoint the broken part of the pipeline (model performance on real data vs. VLM) | Hao | July 15 |
| 2 | Create a debug branch to isolate and analyze quality issues | Hao | July 15 |
| 3 | Propose and implement backend improvements (VLM extraction, linked list data structures) | Benjamin | July 18 |
| 4 | Coordinate with Benjamin and take ownership of frontend design/experience | Wilson | July 20 |
| 5 | Test 2–4 rotation versions of crops to improve VLM robustness | Hao + Benjamin | July 20 |
| 6 | Attend the next team sync | All | Thursday, July 16 @ 6 PM |
| 7 | Ask Alvaro for additional passport scan data for testing | Hao | July 17 |
| 8 | Ensure local Conda environment (`securiport`) is working | All | Before next meeting |

---

*Minutes compiled by Hao Zhang. Agenda and notes archived in `docs/meetings/`.*
