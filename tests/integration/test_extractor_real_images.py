from __future__ import annotations

"""Integration tests for ClaudeExtractor with real stamp image fixtures.

These tests call the real Anthropic API and are skipped automatically
if ANTHROPIC_API_KEY is not set in the environment.

Run with:
    ANTHROPIC_API_KEY=sk-... pytest tests/integration/test_extractor_real_images.py -v
"""

import os

import cv2
import pytest

FIXTURES = "tests/fixtures/stamps"

skip_if_no_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


@pytest.fixture(scope="module")
def extractor():
    from src.ocr.factory import create_extractor_from_config
    return create_extractor_from_config()


def _load(filename: str):
    path = f"{FIXTURES}/{filename}"
    img = cv2.imread(path)
    assert img is not None, f"Could not load {path}"
    return img


# ---------------------------------------------------------------------------
# USA entry stamp — JUN 23 1997  (clear, purple ink, "ADMITTED UNTIL")
# ---------------------------------------------------------------------------

@skip_if_no_key
def test_usa_1997_date(extractor):
    result = extractor.extract(_load("usa_entry_1997.png"))
    assert result.date == "1997-06-23"


@skip_if_no_key
def test_usa_1997_country(extractor):
    result = extractor.extract(_load("usa_entry_1997.png"))
    assert result.country == "USA"


@skip_if_no_key
def test_usa_1997_direction(extractor):
    # "ADMITTED UNTIL" is classic US entry language
    result = extractor.extract(_load("usa_entry_1997.png"))
    assert result.direction == "ENTRY"


@skip_if_no_key
def test_usa_1997_confidence(extractor):
    result = extractor.extract(_load("usa_entry_1997.png"))
    assert result.confidence >= 0.7


# ---------------------------------------------------------------------------
# USA entry stamp — AUG 26 1998  (clear, purple ink, "ADMITTED UNTIL")
# ---------------------------------------------------------------------------

@skip_if_no_key
def test_usa_1998_date(extractor):
    result = extractor.extract(_load("usa_entry_1998.png"))
    assert result.date == "1998-08-26"


@skip_if_no_key
def test_usa_1998_country(extractor):
    result = extractor.extract(_load("usa_entry_1998.png"))
    assert result.country == "USA"


@skip_if_no_key
def test_usa_1998_direction(extractor):
    result = extractor.extract(_load("usa_entry_1998.png"))
    assert result.direction == "ENTRY"


@skip_if_no_key
def test_usa_1998_confidence(extractor):
    result = extractor.extract(_load("usa_entry_1998.png"))
    assert result.confidence >= 0.7


# ---------------------------------------------------------------------------
# Hong Kong arrival stamp — 21 APR 1999  (green ink, "ARRIVED")
# ---------------------------------------------------------------------------

@skip_if_no_key
def test_hongkong_date(extractor):
    result = extractor.extract(_load("hongkong_entry_1999.png"))
    assert result.date == "1999-04-21"


@skip_if_no_key
def test_hongkong_country(extractor):
    result = extractor.extract(_load("hongkong_entry_1999.png"))
    assert result.country == "HKG"


@skip_if_no_key
def test_hongkong_direction(extractor):
    # "ARRIVED" = ENTRY
    result = extractor.extract(_load("hongkong_entry_1999.png"))
    assert result.direction == "ENTRY"


@skip_if_no_key
def test_hongkong_confidence(extractor):
    result = extractor.extract(_load("hongkong_entry_1999.png"))
    assert result.confidence >= 0.7


# ---------------------------------------------------------------------------
# Colombia stamp — 1 JUN 1997  (image is rotated 180°, harder case)
# ---------------------------------------------------------------------------

@skip_if_no_key
def test_colombia_date(extractor):
    # Image is upside-down — VLM should still parse the date
    result = extractor.extract(_load("colombia_entry_1997.png"))
    assert result.date == "1997-06-01"


@skip_if_no_key
def test_colombia_country(extractor):
    result = extractor.extract(_load("colombia_entry_1997.png"))
    assert result.country == "COL"


@skip_if_no_key
def test_colombia_direction(extractor):
    # "INMIGRACION" + "23 DIAS" = entry with 23-day limit
    result = extractor.extract(_load("colombia_entry_1997.png"))
    assert result.direction == "ENTRY"


# ---------------------------------------------------------------------------
# Cross-stamp sanity checks
# ---------------------------------------------------------------------------

@skip_if_no_key
def test_all_stamps_return_extraction_result(extractor):
    from src.ocr.base import ExtractionResult
    stamps = [
        "usa_entry_1997.png",
        "usa_entry_1998.png",
        "hongkong_entry_1999.png",
        "colombia_entry_1997.png",
    ]
    for filename in stamps:
        result = extractor.extract(_load(filename))
        assert isinstance(result, ExtractionResult), f"Wrong return type for {filename}"


@skip_if_no_key
def test_all_stamps_never_raise(extractor):
    stamps = [
        "usa_entry_1997.png",
        "usa_entry_1998.png",
        "hongkong_entry_1999.png",
        "colombia_entry_1997.png",
    ]
    for filename in stamps:
        # Should complete without exception regardless of extraction quality
        extractor.extract(_load(filename))
