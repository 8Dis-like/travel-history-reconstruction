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
│ OCR / VLM        │  PaddleOCR + Qwen-VL / MiniCPM-o
│ Extraction       │  Dates, country, arrival/departure
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
│   ├── ocr/              # Text extraction (PaddleOCR / VLM)
│   ├── reconstruction/   # Timeline assembly & validation
│   ├── api/              # FastAPI service / CLI entry point
│   └── utils/            # Shared utilities
└── tests/                # Unit and integration tests
```

## License

This project is developed as part of the UCLA Master of Science in Engineering Capstone program in partnership with Securiport. All rights reserved.
