from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.ocr.base import BaseExtractor, ExtractionResult
from src.ocr.claude_extractor import ClaudeExtractor


@pytest.fixture
def extractor():
    return ClaudeExtractor(api_key="test-key")


@pytest.fixture
def dummy_image():
    return np.ones((100, 100, 3), dtype=np.uint8) * 200


def _mock_response(text: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def test_claude_extractor_is_base_extractor(extractor):
    assert isinstance(extractor, BaseExtractor)


def test_valid_response_parsed_correctly(extractor, dummy_image):
    payload = json.dumps({
        "date": "2024-03-15",
        "country": "GBR",
        "direction": "ENTRY",
        "raw_text": "HEATHROW 15 MAR 2024 LEAVE TO ENTER",
        "confidence": 0.9,
    })
    with patch.object(extractor._client.messages, "create", return_value=_mock_response(payload)):
        result = extractor.extract(dummy_image)

    assert result.date == "2024-03-15"
    assert result.country == "GBR"
    assert result.direction == "ENTRY"
    assert result.raw_text == "HEATHROW 15 MAR 2024 LEAVE TO ENTER"
    assert result.confidence == 0.9


def test_null_fields_become_none(extractor, dummy_image):
    payload = json.dumps({
        "date": None,
        "country": None,
        "direction": None,
        "raw_text": None,
        "confidence": 0.1,
    })
    with patch.object(extractor._client.messages, "create", return_value=_mock_response(payload)):
        result = extractor.extract(dummy_image)

    assert result.date is None
    assert result.country is None
    assert result.direction is None
    assert result.raw_text is None
    assert result.confidence == 0.1


def test_api_error_returns_all_none_does_not_raise(extractor, dummy_image):
    with patch.object(extractor._client.messages, "create", side_effect=Exception("network error")):
        result = extractor.extract(dummy_image)

    assert isinstance(result, ExtractionResult)
    assert result.date is None
    assert result.country is None
    assert result.direction is None
    assert result.raw_text is None
    assert result.confidence == 0.0


def test_malformed_json_returns_all_none_does_not_raise(extractor, dummy_image):
    with patch.object(extractor._client.messages, "create", return_value=_mock_response("not valid json {")):
        result = extractor.extract(dummy_image)

    assert result.date is None
    assert result.confidence == 0.0


def test_partial_fields_in_response(extractor, dummy_image):
    payload = json.dumps({"date": "2023-11-01", "confidence": 0.6})
    with patch.object(extractor._client.messages, "create", return_value=_mock_response(payload)):
        result = extractor.extract(dummy_image)

    assert result.date == "2023-11-01"
    assert result.country is None
    assert result.direction is None
    assert result.confidence == 0.6
