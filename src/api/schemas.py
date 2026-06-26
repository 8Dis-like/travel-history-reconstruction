from __future__ import annotations

"""Pydantic request/response schemas for the API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ExtractedFields(BaseModel):
    date: Optional[str]
    country: Optional[str]
    direction: Optional[str]
    raw_text: Optional[str]
    extraction_confidence: float


class StampRecord(BaseModel):
    stamp_id: str
    source_image: str
    bounding_box: List[int]          # [x1, y1, x2, y2]
    detection_confidence: float
    extracted_fields: ExtractedFields
    extraction_timestamp: datetime


class PageExtractionResponse(BaseModel):
    source_image: str
    total_stamps_detected: int
    total_stamps_parsed: int
    unreadable_stamps: int
    stamps: List[StampRecord]


class HealthResponse(BaseModel):
    status: str
