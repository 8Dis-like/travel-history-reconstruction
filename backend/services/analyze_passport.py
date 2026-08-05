import numpy as np
from PIL import Image
import cv2
import io
import base64
import torch
from datetime import datetime, timezone

from models import UploadedPageInfo, PageExtractionResponse, ExtractedFields, StampRecord
from detection.stamp_detector import StampDetector, PageProcessingResult
from ocr.factory import create_extractor_from_config


def create_base64_url(img_array: np.ndarray, format: str = "png") -> str:
    if img_array.dtype != np.uint8:
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)

    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    img = Image.fromarray(img_array)

    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)

    b64_str = base64.b64encode(buffer.read()).decode("utf-8")

    mime = f"image/{format.lower()}"
    return f"data:{mime};base64,{b64_str}"


def analyze_passport(pages: list[UploadedPageInfo]) -> list[PageExtractionResponse]:
    passport_response = []
    extract = False # REMOVE REMOVE REMOVE

    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    task = "segment"

    page_images = [page.image for page in pages]
    stamp_detector = StampDetector(device=device, task=task)
    stamp_extractor = create_extractor_from_config()

    page_detection_results: list[PageProcessingResult] = stamp_detector.detect(page_images)

    for page, page_detection_result in zip(pages, page_detection_results):
        stamps = []
        for i, stamp in enumerate(page_detection_result.page_stamps):
            if extract:
                extraction = stamp_extractor.extract(stamp.stamp_img)
                is_parsed = any([extraction.date, extraction.country, extraction.direction])
                if not is_parsed:
                    if extraction.confidence <= 0.2:
                        page_detection_result.total_stamps_detected -= 1
                        continue
                    else:
                        total_unreadable += 1

                extraction_result = ExtractedFields(
                    date=extraction.date,
                    country=extraction.country,
                    direction=extraction.direction,
                    raw_text=extraction.raw_text,
                    extraction_confidence=extraction.confidence,
                )
            else:
                extraction_result = ExtractedFields(
                    date="",
                    country="",
                    direction="",
                    raw_text="",
                    extraction_confidence=0.5,
                )

            stamp_record = StampRecord(
                stamp_id=f"{page.source_filename}_stamp{i}",
                stamp_image=create_base64_url(stamp.stamp_img),
                bounding_box=stamp.bounding_box,
                mask=stamp.mask if task == "segment" else [],
                detection_confidence=stamp.confidence,
                extracted_fields=extraction_result,
                page_source=page.source_filename,
                page_number=page.page_number,
                # extraction_timestamp=datetime.now(timezone.utc),
            )

            stamps.append(stamp_record)

        page_response = PageExtractionResponse(
            source_filename=page.source_filename,
            page_number=page.page_number,
            processed_image=create_base64_url(page_detection_result.processed_img),
            total_stamps_detected=page_detection_result.total_stamps_detected,
            total_stamps_parsed=0,
            unreadable_stamps=0,
            stamps=stamps,
        )

        passport_response.append(page_response)

    return passport_response
