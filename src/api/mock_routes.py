from __future__ import annotations

"""Mock extraction endpoint — returns fixed fake data until the real recognition module is ready."""

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter()


class MockExtractedRecord(BaseModel):
    date: str | None
    country: str | None
    direction: str | None
    raw_text: str | None
    confidence: float


class MockPdfExtractionResponse(BaseModel):
    source_file: str
    records: list[MockExtractedRecord]


_FIXED_RECORDS = [
    MockExtractedRecord(date="2024-01-10", country="USA", direction="EXIT", raw_text="LAX 10 JAN 2024", confidence=0.92),
    MockExtractedRecord(date="2024-01-11", country="GBR", direction="ENTRY", raw_text="HEATHROW 11 JAN 2024", confidence=0.88),
    MockExtractedRecord(date="2024-02-20", country="GBR", direction="EXIT", raw_text="HEATHROW 20 FEB 2024", confidence=0.61),
    MockExtractedRecord(date=None, country=None, direction=None, raw_text=None, confidence=0.0),
]


@router.post("/extract/mock/pdf", response_model=MockPdfExtractionResponse)
async def extract_mock_pdf(file: UploadFile = File(...)):
    """Fake stand-in for the real recognition pipeline.

    Accepts a PDF, ignores its content, and always returns the same fixed
    fake records tagged with the uploaded filename. Swap this handler's
    body for a real call into src/ocr + src/detection when ready.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only application/pdf uploads are accepted.")
    return MockPdfExtractionResponse(source_file=file.filename or "upload.pdf", records=_FIXED_RECORDS)
