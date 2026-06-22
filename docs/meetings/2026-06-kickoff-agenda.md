# 📋 Team Kickoff Meeting — Agenda

**Project:** Travel History Reconstruction from Travel Documents
**Meeting Type:** Sprint Kickoff & Coordination Sync
**Duration:** ~30 min
**Date/Time:** 7 p.m. PST, June 22

---

## 1. Where We Are (5 min) — Hao

Quick recap of progress to date:

- ✅ GitHub repo set up and running: [travel-history-reconstruction](https://github.com/8Dis-like/travel-history-reconstruction)
- ✅ Proposal finalized and shared on Notion
- ✅ Preprocessing pipeline (`enhancer.py`) — handles auto-orientation (90°/180°/270°), deskewing, CLAHE contrast enhancement
- ✅ Stamp detection wrapper (`stamp_detector.py`) — YOLOv8 inference pipeline, structured output, crop extraction, visualization
- ✅ Pipeline smoke test validated on first batch of sample data (38 passport page images received from Securiport)
- ✅ Baseline result: preprocessing works, COCO model detects 0 stamps (expected — no "stamp" class in COCO)

**Key observation from sample data:** Many pages are rotated 90°, stamps are multilingual (Spanish, English, French), and several pages have overlapping stamps.

---

## 2. The Road Ahead (10 min) — All

Walk through our staged milestones and agree on immediate priorities:

| Stage | Goal | Status |
|---|---|---|
| **Stage 1** — Stamp Detection & Isolation | Detect all stamp regions, output crops | 🟡 In Progress |
| **Stage 2** — Date Extraction | Extract dates from each stamp (English) | ⬜ Not Started |
| **Stage 3** — Full Field Extraction | Country + direction via VLM | ⬜ Not Started |
| **Stage 4** — Timeline Reconstruction | Chronological travel history | ⬜ Not Started |
| **Stage 5** — Multilingual & Production | Stretch goal | ⬜ Not Started |

### Immediate Sprint Focus (Weeks 3–4)

The critical blocker right now is **Stage 1 completion**. Discussion points:

1. **Data Annotation** — How many of the 38 pages should we annotate first? What tool (Roboflow vs. CVAT)? Who does what?
2. **YOLOv8 Fine-Tuning** — Target: get mAP ≥ 0.70 on a held-out test split. Compute plan (local GPU vs. Colab Pro)?
3. **OCR Integration** — Zuyan can start PaddleOCR integration in parallel (no dependency on detection fine-tuning).
4. **External Data** — Should we supplement with Roboflow Universe stamp datasets to boost training volume?

---

## 3. Work Split (5 min) — All

Review and confirm the role assignments from the proposal:

| Member | Primary Ownership | Weeks 3–4 Focus |
|---|---|---|
| **Hao Zhang** | Preprocessing + Detection | Fine-tune YOLOv8 on annotated stamps; iterate on detection mAP |
| **Zuyan Tao** | OCR + Backend | Integrate PaddleOCR; build date extraction regex pipeline |
| **Wilson Tee** | Data + Frontend | Annotate stamp bounding boxes in sample data; curate external datasets |

### Dependencies to Discuss

- Wilson's annotations → feed into Hao's training (critical path)
- Hao's detection crops → feed into Zuyan's OCR pipeline
- Agree on annotation format (YOLO `.txt`) and directory conventions (`data/annotations/`)

---

## 4. Coordination Methods (5 min) — All

Agree on how we work together going forward:

### Communication

| Channel | Purpose | Frequency |
|---|---|---|
| **Whatsapp** | Quick questions, daily coordination | As needed |
| **Notion** | Docs, meeting notes, task tracking (Kanban) | Ongoing |
| **GitHub PRs** | Code reviews (≥1 approval required) | Per feature |

### Meetings

| Meeting | Cadence | Duration | Purpose |
|---|---|---|---|
| **Team standup** | Weekly (Monday?) | 30 min | Progress sync, blockers, next steps |
| **Sponsor check-in** | Bi-weekly | 30 min | Demo progress to Alvaro |

### Git Workflow

- **Branching:** Feature branches off `master` → PR → review → merge
- **Naming:** `feat/stamp-annotation`, `feat/paddleocr-integration`, etc.
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`, `test:`)

### Notion Setup

- Import proposal page (already done)
- Create a **Sprint Board** (Kanban) with columns: Backlog → In Progress → Review → Done
- Each member creates task cards for their Week 3–4 deliverables

---

## 5. Action Items & Next Steps (5 min) — Hao

Wrap up with concrete takeaways. Template:

| # | Action Item | Owner | Due |
|---|---|---|---|
| 1 | Set up annotation tool (Roboflow) and annotate first 10 pages | Wilson | Week 3 |
| 2 | Source and merge Roboflow Universe stamp datasets | Wilson | Week 3 |
| 3 | Start YOLOv8 fine-tuning once ≥20 annotated images ready | Hao | Week 3–4 |
| 4 | Set up PaddleOCR and test on sample stamp crops (manual crops for now) | Zuyan | Week 3 |
| 5 | Create Notion sprint board with Week 3–4 task cards | Hao | This week |
| 6 | Schedule first sponsor check-in with Alvaro | Hao | This week |
| 7 | Everyone: clone repo, run `pip install -r requirements.txt`, run `test_pipeline.py` | All | Before next standup |

---

## Pre-Read Materials

Please review these before the meeting:

1. 📄 [Project Proposal](../proposal.md) — especially Sections 3 (Staged Milestones), 8 (Work Breakdown), and 9 (Timeline)
2. 🔍 [Pipeline Verification Guide](../reports/pipeline_verification_guide.md) — step-by-step instructions to run and verify the current pipeline locally
3. 📊 [Pipeline Validation Report](../reports/pipeline_validation_report.md) — results from the first smoke test on sample data
