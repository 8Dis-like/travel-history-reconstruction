"""OCR module — text extraction from stamp images."""

from src.ocr.base import BaseExtractor, ExtractionResult
from src.ocr.factory import create_extractor

__all__ = ["BaseExtractor", "ExtractionResult", "create_extractor"]
