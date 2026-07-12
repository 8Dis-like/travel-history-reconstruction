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
from src.detection.stamp_detector import StampDetector
from src.ocr.factory import create_extractor
from src.preprocessing.enhancer import ImageEnhancer

router = APIRouter()

_enhancer = ImageEnhancer()
_detector = StampDetector(model_path="runs/best_stamp_model.pt")
import os
_extractor = create_extractor(os.getenv("OCR_PROVIDER", "deepseek"))


import fitz  # PyMuPDF

def _decode_uploads(data: bytes, filename: str) -> list[tuple[str, np.ndarray]]:
    if filename.lower().endswith(".pdf"):
        try:
            doc = fitz.open("pdf", data)
            images = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # dpi=300 for good quality OCR/detection
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                if pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                elif pix.n == 1:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                images.append((f"page_{page_num+1}_{filename}", img))
            return images
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")
    else:
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Could not decode image — send a valid PNG, JPEG, or PDF.")
        return [(filename, img)]


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@router.post("/extract/stamp", response_model=ExtractedFields)
async def extract_stamp(file: UploadFile = File(...)):
    """Extract fields from a single pre-cropped stamp image."""
    filename = file.filename or "upload.png"
    images = _decode_uploads(await file.read(), filename)
    if not images:
        raise HTTPException(status_code=400, detail="No images found.")
    _, img = images[0]
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
    """Run the full pipeline on a passport page image or PDF.

    Upload a PNG, JPEG, or PDF. Returns all detected stamps.
    """
    filename = file.filename or "upload.png"
    images = _decode_uploads(await file.read(), filename)

    all_stamps = []
    total_detected = 0
    total_unreadable = 0

    for page_name, raw_img in images:
        enhanced, _ = _enhancer.process(raw_img)
        detection_result = _detector.detect(enhanced, extract_crops=True, source_name=page_name)
        
        total_detected += len(detection_result.detections)

        for det in detection_result.detections:
            if det.crop is None:
                continue

            extraction = _extractor.extract(det.crop)
            x1, y1, x2, y2 = det.bbox_xyxy
            is_parsed = any([extraction.date, extraction.country, extraction.direction])
            if not is_parsed:
                total_unreadable += 1

            all_stamps.append(StampRecord(
                stamp_id=det.stamp_id,
                source_image=page_name,
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
        total_stamps_detected=total_detected,
        total_stamps_parsed=len(all_stamps) - total_unreadable,
        unreadable_stamps=total_unreadable,
        stamps=all_stamps,
    )
