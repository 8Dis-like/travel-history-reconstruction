from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Literal
import numpy as np

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class ExtractedFields(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    date: Optional[str]
    country: Optional[str]
    direction: Optional[str]
    raw_text: Optional[str]
    extraction_confidence: float


class StampRecord(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    stamp_id: str
    stamp_image: str
    bounding_box: List[int]          # [x1, y1, x2, y2]
    mask: Optional[List[List[int]]]
    detection_confidence: float
    extracted_fields: ExtractedFields
    page_source: str
    page_number: int
    # extraction_timestamp: datetime


class PageExtractionResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    source_filename: str
    page_number: int
    processed_image: str
    total_stamps_detected: int
    total_stamps_parsed: int
    unreadable_stamps: int
    stamps: List[StampRecord]


class StayResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    stay_id: str
    country: Optional[str]
    entry_date: Optional[str]
    exit_date: Optional[str]
    entry_stamp: Optional[StampRecord]
    exit_stamp: Optional[StampRecord]
    status: Literal["confirmed", "inferred", "flagged"]
    flags: List[str]


class TravelHistoryResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    stays: List[StayResponse]
    unattributable_stamps: List[StampRecord]


class HealthResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str


@dataclass
class UploadedPageInfo:
    source_filename: str
    page_number: int
    image: np.ndarray
