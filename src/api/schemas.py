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


class TimelineEventOut(BaseModel):
    date: Optional[str]
    country: Optional[str]
    direction: Optional[str]
    stamp_id: Optional[str] = None
    source_image: Optional[str] = None


class TimelineOut(BaseModel):
    events: List[TimelineEventOut]   # placeable events, ascending by date
    undated: List[TimelineEventOut]  # missing / invalid date, order preserved


def timeline_to_out(timeline) -> TimelineOut:
    """Convert a reconstruction.Timeline into its API response schema."""
    def conv(e) -> TimelineEventOut:
        return TimelineEventOut(
            date=e.date,
            country=e.country,
            direction=e.direction,
            stamp_id=e.stamp_id,
            source_image=e.source_image,
        )

    return TimelineOut(
        events=[conv(e) for e in timeline.events],
        undated=[conv(e) for e in timeline.undated],
    )


class PageExtractionResponse(BaseModel):
    source_image: str
    total_stamps_detected: int
    total_stamps_parsed: int
    unreadable_stamps: int
    stamps: List[StampRecord]
    timeline: TimelineOut


class HealthResponse(BaseModel):
    status: str
