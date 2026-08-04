"""OCR module — text extraction from stamp images."""

from ocr.base import BaseExtractor, ExtractionResult
from ocr.factory import create_extractor

__all__ = ["BaseExtractor", "ExtractionResult", "create_extractor"]
