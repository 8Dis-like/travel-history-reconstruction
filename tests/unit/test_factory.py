from __future__ import annotations

import pytest


def test_creates_claude_extractor():
    from src.ocr.claude_extractor import ClaudeExtractor
    from src.ocr.factory import create_extractor
    extractor = create_extractor("claude", api_key="test-key")
    assert isinstance(extractor, ClaudeExtractor)


def test_creates_local_extractor():
    from src.ocr.local_extractor import LocalVLMExtractor
    from src.ocr.factory import create_extractor
    extractor = create_extractor("local")
    assert isinstance(extractor, LocalVLMExtractor)


def test_unknown_provider_raises_value_error():
    from src.ocr.factory import create_extractor
    with pytest.raises(ValueError, match="unknown provider"):
        create_extractor("paddleocr")


def test_returned_extractor_is_base_extractor_subclass():
    from src.ocr.base import BaseExtractor
    from src.ocr.factory import create_extractor
    extractor = create_extractor("local")
    assert isinstance(extractor, BaseExtractor)
