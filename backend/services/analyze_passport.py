import numpy as np
from PIL import Image
import cv2
import io
import base64
import torch
from datetime import datetime, timezone
from typing import Dict
import uuid

from models import UploadedPageInfo, PageExtractionResponse, ExtractedFields, StampRecord, PageExtractionMetadata
from detection.stamp_detector import StampDetector, PageProcessingResult
from ocr.factory import create_extractor_from_config
from helpers import create_base64_url, is_valid_date


def analyze_passport(pages: Dict[str, UploadedPageInfo]) -> tuple[dict[str, StampRecord], dict[str, PageExtractionMetadata]]:
    pages_metadata = dict()
    stamps = dict()

    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    task = "segment"

    page_images = [page.image for page in pages.values()]
    stamp_detector = StampDetector(device=device, task=task)
    stamp_extractor = create_extractor_from_config()

    page_detection_results: list[PageProcessingResult] = stamp_detector.detect(page_images)

    for page_id, page_detection_result in zip(pages.keys(), page_detection_results):
        unreadable_stamps = 0

        for i, stamp in enumerate(page_detection_result.page_stamps):
            b64_stamp = create_base64_url(stamp.stamp_img)
            extraction = stamp_extractor.extract(b64_stamp)
            is_parsed = any([extraction.date, extraction.country, extraction.direction])
            if not is_parsed:
                unreadable_stamps += 1

            parsed_date = extraction.date

            if parsed_date is not None and is_valid_date(parsed_date):
                parsed_date = extraction.date
            else:
                parsed_date = None

            extraction_result = ExtractedFields(
                date=parsed_date,
                country=extraction.country,
                direction=extraction.direction,
                raw_text= None, # extraction.raw_text,
                extraction_confidence=extraction.confidence,
            )

            print(f"Extracted Stamp {i} (Date: {extraction_result.date}, Country: {extraction_result.country}, Direction: {extraction_result.direction})")

            stamp_id = str(uuid.uuid4())

            stamp_record = StampRecord(
                stamp_id=stamp_id,
                stamp_image=b64_stamp,
                bounding_box=stamp.bounding_box,
                mask=stamp.mask if task == "segment" else [],
                detection_confidence=stamp.confidence,
                extracted_fields=extraction_result,
                original_fields=extraction_result,
                page_id=page_id,
                extraction_timestamp=datetime.now(timezone.utc),
            )

            stamps[stamp_id] = stamp_record

        page_metadata = PageExtractionMetadata(
            processed_image=create_base64_url(page_detection_result.processed_img),
            image_width=page_detection_result.image_width,
            image_height=page_detection_result.image_height,
            total_stamps_detected=page_detection_result.total_stamps_detected,
            total_stamps_parsed=page_detection_result.total_stamps_detected - unreadable_stamps,
            unreadable_stamps=unreadable_stamps,
        )

        pages_metadata[page_id] = page_metadata

    return (stamps, pages_metadata)
