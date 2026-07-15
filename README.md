# Travel History Reconstruction from Travel Documents

**UCLA MSEng Capstone Project** | Sponsored by [Securiport](https://www.securiport.com/)

## Overview

An end-to-end system that takes scanned passport page images as input, detects and segments visa/entry stamps, extracts dates, country codes, and arrival/departure indicators via OCR, and reconstructs a structured, chronological travel history for a given subject.

## Team

| Member | Role |
|--------|------|
| **Hao Zhang** | Team Coordinator & ML Pipeline Lead |
| **Zuyan Tao** | Agentic Backend & System Integration |
| **Wilson Tee** | Frontend, Data Engineering & Evaluation |

**Sponsor:** Alvaro Ramirez — Securiport

## Resources

* **[Notion Teamspace Home](https://app.notion.com/p/Teamspace-Home-d4aa80630d0d8333970c81695be329f6?source=copy_link)**: Central hub for project planning, task tracking, and meeting notes.

## Project Architecture

```
Scanned Passport Image
        │
        ▼
┌─────────────────┐
│  Preprocessing   │  Deskew, denoise, enhance contrast
└────────┬────────┘
         ▼
┌─────────────────┐
│ Stamp Detection  │  YOLOv8 / RT-DETR object detection
└────────┬────────┘
         ▼
┌─────────────────┐
│ Stamp Isolation  │  Crop & segment individual stamps
└────────┬────────┘
         ▼
┌─────────────────┐
│ VLM Extraction   │  Claude Vision (model set in configs/pipeline.yaml)
│                  │  Dates, country, arrival/departure — no separate OCR layer
└────────┬────────┘
         ▼
┌─────────────────┐
│ Timeline         │  Chronological ordering, validation
│ Reconstruction   │  Conflict resolution, confidence scores
└────────┬────────┘
         ▼
   Structured Travel History (JSON / Report)
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/<org>/travel-history-reconstruction.git
cd travel-history-reconstruction

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the pipeline on a sample image
python -m src.api.main --input data/raw/sample_passport.jpg
```

## Project Structure

```
├── configs/              # YAML configs for models, pipeline params
├── data/
│   ├── raw/              # Original scanned passport images
│   ├── processed/        # Preprocessed images
│   └── annotations/      # Labeling data (YOLO format)
├── docs/                 # Proposal, reports, meeting notes
├── models/
│   ├── pretrained/       # Downloaded base models
│   └── finetuned/        # Fine-tuned checkpoints
├── notebooks/            # Jupyter notebooks for experimentation
├── scripts/              # Utility scripts (data download, eval)
├── src/
│   ├── preprocessing/    # Image enhancement pipeline
│   ├── detection/        # Stamp detection (YOLO)
│   ├── ocr/              # VLM field extraction (Claude Vision; config-driven factory)
│   ├── reconstruction/   # Timeline assembly & validation
│   ├── api/              # FastAPI service / CLI entry point
│   └── utils/            # Shared utilities
└── tests/                # Unit and integration tests
```

## Field Extraction & Configuration

Stamp field extraction (date, country, direction, raw text, confidence) is done
by a **vision-language model, not a traditional OCR layer** — the VLM handles
varied date formats, faded ink, and multilingual text in a single call.

**The model is config-driven — it is never hardcoded.** The extractor is built
by a factory that reads the `ocr` section of `configs/pipeline.yaml`:

```yaml
ocr:
  engine: "claude"          # selects the provider (claude | local)
  claude:
    model: "claude-sonnet-5"
    max_tokens: 256
```

`create_extractor_from_config()` (`src/ocr/factory.py`) reads `ocr.engine` and
the matching `ocr.<engine>` sub-block, then constructs the extractor. To switch
models or providers, **edit `pipeline.yaml` only — no code change.** `model` is a
required constructor argument (`ClaudeExtractor`), so a misconfigured pipeline
fails loudly instead of silently falling back to some default.

**Design notes:**

- **No CV-based rotation correction (deskew).** An earlier per-stamp deskew step
  was prototyped and removed: measured end-to-end, it *lowered* accuracy (it
  corrupted already-upright crops), because the VLM already tolerates rotation.
  The residual failures were misread date digits, not orientation — i.e. the
  bottleneck was model capability, not rotation. On the rotation-robustness
  benchmark (`scripts/test_rotation_robustness.py`), `claude-haiku-4-5` scored
  15/20 while `claude-sonnet-5` scored 20/20 on the same rotated fixtures, so the
  default model is Sonnet and no deskew is applied.
- `local` (`LocalVLMExtractor`, e.g. MiniCPM-o / Qwen-VL) is a stub for a future
  offline provider; the factory already supports selecting it via config.

## License

This project is developed as part of the UCLA Master of Science in Engineering Capstone program in partnership with Securiport. All rights reserved.
