from __future__ import annotations

"""API route handlers."""

import io
from datetime import datetime, timezone

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile

from src.api.schemas import (
    ExtractedFields,
    HealthResponse,
    PageExtractionResponse,
    StampRecord,
)
from src.detection.mock_detector import MockStampDetector
from src.ocr.factory import create_extractor
from src.preprocessing.enhancer import ImageEnhancer

router = APIRouter()

_enhancer = ImageEnhancer()
_detector = MockStampDetector()
_extractor = create_extractor("claude")


def _decode_upload(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not decode image — send a valid PNG or JPEG.")
    return img


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@router.post("/extract/stamp", response_model=ExtractedFields)
async def extract_stamp(file: UploadFile = File(...)):
    """Extract fields from a single pre-cropped stamp image.

    Upload a PNG or JPEG of a single stamp crop.
    Returns date, country, direction, raw_text, and confidence.
    """
    img = _decode_upload(await file.read())
    result = _extractor.extract(img)
    return ExtractedFields(
        date=result.date,
        country=result.country,
        direction=result.direction,
        raw_text=result.raw_text,
        extraction_confidence=result.confidence,
    )


@router.post("/extract/page", response_model=PageExtractionResponse)
async def extract_page(file: UploadFile = File(...)):
    """Run the full pipeline on a passport page image.

    Upload a PNG or JPEG of a passport page.
    Returns all detected stamps with extracted fields.

    Note: Uses MockStampDetector until fine-tuned YOLOv8 weights are available.
    """
    raw_img = _decode_upload(await file.read())
    filename = file.filename or "upload.png"

    enhanced, _ = _enhancer.process(raw_img)
    detection_result = _detector.detect(enhanced, extract_crops=True, source_name=filename)

    stamps = []
    unreadable = 0

    for det in detection_result.detections:
        if det.crop is None:
            continue

        extraction = _extractor.extract(det.crop)
        x1, y1, x2, y2 = det.bbox_xyxy
        is_parsed = any([extraction.date, extraction.country, extraction.direction])
        if not is_parsed:
            unreadable += 1

        stamps.append(StampRecord(
            stamp_id=det.stamp_id,
            source_image=filename,
            bounding_box=[x1, y1, x2, y2],
            detection_confidence=det.confidence,
            extracted_fields=ExtractedFields(
                date=extraction.date,
                country=extraction.country,
                direction=extraction.direction,
                raw_text=extraction.raw_text,
                extraction_confidence=extraction.confidence,
            ),
            extraction_timestamp=datetime.now(timezone.utc),
        ))

    return PageExtractionResponse(
        source_image=filename,
        total_stamps_detected=len(detection_result.detections),
        total_stamps_parsed=len(stamps) - unreadable,
        unreadable_stamps=unreadable,
        stamps=stamps,
    )
