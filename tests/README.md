# Testing Strategy & Structure

This directory contains the test suite for the Travel History Reconstruction pipeline, organized according to software engineering best practices. 

## Structure

```
tests/
├── unit/                 # Unit tests for isolated components (e.g., individual regex parsers, single enhancement functions)
├── integration/          # Integration tests verifying the docking between modules (CRITICAL: Hao's detection outputs -> Zuyan's OCR inputs)
├── e2e/                  # End-to-end tests running the full pipeline from raw image to final JSON output
├── fixtures/             # Mock data, sample images, and expected JSON outputs for testing
├── conftest.py           # Shared pytest fixtures (e.g., mock models, temporary directories)
└── README.md             # This document
```

## Core Docking: Detection (Hao) ↔ OCR (Zuyan)

The most critical interaction in the pipeline is the interface between the **Detection module** (Hao) and the **OCR module** (Zuyan). 
To ensure this docking remains stable, integration tests must strictly define the expected input/output contract:

1. **Detection Output**: Hao's module must return an object or array containing:
    * Bounding box coordinates
    * Cropped numpy array of the stamp
    * Detection confidence score
2. **OCR Input**: Zuyan's module must accept the cropped numpy array (and optionally the bounding box context) without requiring disk I/O.

See `tests/integration/test_docking_detection_ocr.py` for the explicit contract test.

## Running Tests

We use `pytest` for all testing.

**Run all tests:**
```bash
pytest
```

**Run specific test categories:**
```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

**Run with coverage:**
```bash
pytest --cov=src tests/
```
