from __future__ import annotations

import numpy as np
import pytest


def test_base_extractor_cannot_be_instantiated():
    from src.ocr.base import BaseExtractor
    with pytest.raises(TypeError):
        BaseExtractor()


def test_extraction_result_all_fields_present():
    from src.ocr.base import ExtractionResult
    result = ExtractionResult(
        date="2024-03-15",
        country="GBR",
        direction="ENTRY",
        raw_text="HEATHROW 15 MAR 2024",
        confidence=0.9,
    )
    assert result.date == "2024-03-15"
    assert result.country == "GBR"
    assert result.direction == "ENTRY"
    assert result.raw_text == "HEATHROW 15 MAR 2024"
    assert result.confidence == 0.9


def test_extraction_result_all_none_is_valid():
    from src.ocr.base import ExtractionResult
    result = ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)
    assert result.date is None
    assert result.country is None
    assert result.direction is None
    assert result.raw_text is None
    assert result.confidence == 0.0


def test_local_extractor_satisfies_abc():
    from src.ocr.base import BaseExtractor
    from src.ocr.local_extractor import LocalVLMExtractor
    extractor = LocalVLMExtractor()
    assert isinstance(extractor, BaseExtractor)


def test_local_extractor_extract_raises_not_implemented():
    from src.ocr.local_extractor import LocalVLMExtractor
    extractor = LocalVLMExtractor()
    dummy = np.ones((100, 100, 3), dtype=np.uint8)
    with pytest.raises(NotImplementedError):
        extractor.extract(dummy)
