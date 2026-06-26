# OCR/VLM Extractor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a factory-pattern VLM extractor that accepts stamp crop numpy arrays and returns structured `ExtractionResult` objects, with Claude Haiku as the active provider and a LocalVLM stub.

**Architecture:** `BaseExtractor` ABC defines the interface; `ClaudeExtractor` encodes images to base64 and calls the Anthropic API; `LocalVLMExtractor` is a stub that satisfies the ABC but raises `NotImplementedError`. A factory function maps provider name strings to instances. All tests are written before implementation (TDD).

**Tech Stack:** Python 3.11+, `anthropic` SDK, `opencv-python`, `numpy`, `pytest`, `unittest.mock`

## Global Constraints

- Python 3.11+ (`str | None` union syntax, no `Optional`)
- `from __future__ import annotations` at top of every file in `src/` (existing codebase convention — see `mock_detector.py`)
- Input images are BGR numpy arrays, dtype `uint8`, shape `(H, W, 3)` — same format as `StampDetection.crop`
- `extract()` never raises — errors → all-None `ExtractionResult` with `confidence=0.0`
- All tests use `unittest.mock` (already available via stdlib, no extra dep)
- Model: `claude-haiku-4-5-20251001`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/ocr/base.py` | Create | `ExtractionResult` dataclass + `BaseExtractor` ABC |
| `src/ocr/local_extractor.py` | Create | `LocalVLMExtractor` stub |
| `src/ocr/claude_extractor.py` | Create | `ClaudeExtractor` — Anthropic API call |
| `src/ocr/factory.py` | Create | `create_extractor(provider, **kwargs)` |
| `src/ocr/__init__.py` | Modify | Export public API |
| `requirements.txt` | Modify | Add `anthropic>=0.25.0` |
| `tests/unit/test_interface_contract.py` | Create | ABC + dataclass contract tests |
| `tests/unit/test_factory.py` | Create | Factory routing tests |
| `tests/unit/test_claude_extractor.py` | Create | Mocked API tests |
| `tests/integration/test_extractor_real_images.py` | Create | Skipped skeleton — unskip when fixtures arrive |

---

### Task 1: `ExtractionResult` dataclass + `BaseExtractor` ABC

**Files:**
- Create: `src/ocr/base.py`
- Create: `tests/unit/__init__.py` (empty, needed for pytest discovery)
- Create: `tests/unit/test_interface_contract.py`

**Interfaces:**
- Produces: `ExtractionResult(date, country, direction, raw_text, confidence)` and `BaseExtractor` used by all subsequent tasks

- [ ] **Step 1: Create `tests/unit/__init__.py`**

```python
```
(empty file)

- [ ] **Step 2: Write the failing tests**

Create `tests/unit/test_interface_contract.py`:

```python
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
```

- [ ] **Step 3: Run to verify they fail**

```bash
pytest tests/unit/test_interface_contract.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` (module doesn't exist yet)

- [ ] **Step 4: Create `src/ocr/base.py`**

```python
from __future__ import annotations

"""Base interface for all stamp field extractors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ExtractionResult:
    date: str | None
    country: str | None
    direction: str | None
    raw_text: str | None
    confidence: float


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, image: np.ndarray) -> ExtractionResult:
        """Extract structured fields from a stamp crop.

        Args:
            image: BGR numpy array, shape (H, W, 3), dtype uint8.

        Returns:
            ExtractionResult — unreadable fields set to None, never raises.
        """
```

- [ ] **Step 5: Run to verify tests pass**

```bash
pytest tests/unit/test_interface_contract.py -v
```

Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add src/ocr/base.py tests/unit/__init__.py tests/unit/test_interface_contract.py
git commit -m "feat(ocr): add ExtractionResult dataclass and BaseExtractor ABC"
```

---

### Task 2: `LocalVLMExtractor` stub

**Files:**
- Create: `src/ocr/local_extractor.py`
- Modify: `tests/unit/test_interface_contract.py` (add LocalVLM tests)

**Interfaces:**
- Consumes: `BaseExtractor`, `ExtractionResult` from `src/ocr/base.py`
- Produces: `LocalVLMExtractor` used by factory in Task 4

- [ ] **Step 1: Add failing tests to `tests/unit/test_interface_contract.py`**

Append these tests to the existing file:

```python
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/unit/test_interface_contract.py::test_local_extractor_satisfies_abc -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Create `src/ocr/local_extractor.py`**

```python
from __future__ import annotations

"""Local VLM extractor stub — not yet implemented."""

import numpy as np

from src.ocr.base import BaseExtractor, ExtractionResult


class LocalVLMExtractor(BaseExtractor):
    """Placeholder for a locally-hosted VLM (e.g. MiniCPM-o, Qwen-VL).

    Not implemented. Swap in when model weights are available.
    """

    def extract(self, image: np.ndarray) -> ExtractionResult:
        raise NotImplementedError(
            "LocalVLMExtractor is not yet implemented. Use provider='claude' instead."
        )
```

- [ ] **Step 4: Run to verify tests pass**

```bash
pytest tests/unit/test_interface_contract.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/ocr/local_extractor.py tests/unit/test_interface_contract.py
git commit -m "feat(ocr): add LocalVLMExtractor stub"
```

---

### Task 3: Factory

**Files:**
- Create: `src/ocr/factory.py`
- Create: `tests/unit/test_factory.py`

**Interfaces:**
- Consumes: `ClaudeExtractor` (Task 4), `LocalVLMExtractor` (Task 2), `BaseExtractor` (Task 1)
- Produces: `create_extractor(provider: str, **kwargs) -> BaseExtractor`

> Note: `ClaudeExtractor` does not exist yet. Write the factory and its tests now — they will fail until Task 4 is done. That's expected TDD flow.

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_factory.py`:

```python
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/unit/test_factory.py -v
```

Expected: `ModuleNotFoundError` for `src.ocr.factory` and `src.ocr.claude_extractor`

- [ ] **Step 3: Create `src/ocr/factory.py`**

```python
from __future__ import annotations

"""Factory for creating extractor instances by provider name."""

from src.ocr.base import BaseExtractor


def create_extractor(provider: str, **kwargs) -> BaseExtractor:
    """Create an extractor for the given provider.

    Args:
        provider: "claude" or "local"
        **kwargs: Passed to the provider constructor.
                  For "claude": api_key (str, optional — falls back to ANTHROPIC_API_KEY env var)

    Raises:
        ValueError: If provider is not recognized.
    """
    if provider == "claude":
        from src.ocr.claude_extractor import ClaudeExtractor
        return ClaudeExtractor(**kwargs)
    if provider == "local":
        from src.ocr.local_extractor import LocalVLMExtractor
        return LocalVLMExtractor(**kwargs)
    raise ValueError(f"unknown provider '{provider}' — choose 'claude' or 'local'")
```

- [ ] **Step 4: Run factory tests that don't need ClaudeExtractor**

```bash
pytest tests/unit/test_factory.py::test_creates_local_extractor tests/unit/test_factory.py::test_unknown_provider_raises_value_error tests/unit/test_factory.py::test_returned_extractor_is_base_extractor_subclass -v
```

Expected: 3 passed. `test_creates_claude_extractor` will still fail (ClaudeExtractor not yet created) — that's fine.

- [ ] **Step 5: Commit**

```bash
git add src/ocr/factory.py tests/unit/test_factory.py
git commit -m "feat(ocr): add extractor factory"
```

---

### Task 4: `ClaudeExtractor`

**Files:**
- Create: `src/ocr/claude_extractor.py`
- Create: `tests/unit/test_claude_extractor.py`
- Modify: `requirements.txt` (add `anthropic`)

**Interfaces:**
- Consumes: `BaseExtractor`, `ExtractionResult` from `src/ocr/base.py`
- Produces: `ClaudeExtractor(api_key=None, model="claude-haiku-4-5-20251001")` with `.extract(image: np.ndarray) -> ExtractionResult`

- [ ] **Step 1: Add `anthropic` to `requirements.txt`**

In the `# OCR` section, replace the comment block with:

```
# ==============================
# OCR
# ==============================
anthropic>=0.25.0
```

- [ ] **Step 2: Install the dependency**

```bash
pip install anthropic>=0.25.0
```

- [ ] **Step 3: Write the failing tests**

Create `tests/unit/test_claude_extractor.py`:

```python
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
```

- [ ] **Step 4: Run to verify they fail**

```bash
pytest tests/unit/test_claude_extractor.py -v
```

Expected: `ModuleNotFoundError` for `src.ocr.claude_extractor`

- [ ] **Step 5: Create `src/ocr/claude_extractor.py`**

```python
from __future__ import annotations

"""VLM extractor using the Anthropic Claude API."""

import base64
import json

import cv2
import numpy as np
import anthropic

from src.ocr.base import BaseExtractor, ExtractionResult

_PROMPT = """\
Analyze this passport stamp image and extract the following fields:
- date: the date in ISO 8601 format YYYY-MM-DD
- country: the ISO-3166 alpha-3 country code (e.g. GBR, USA, FRA)
- direction: exactly "ENTRY" or "EXIT"
- raw_text: all visible text in the stamp exactly as it appears
- confidence: your confidence as a float 0.0–1.0

Return ONLY a JSON object with these exact keys. Set any unreadable field to null.
Example: {"date": "2024-03-15", "country": "GBR", "direction": "ENTRY", "raw_text": "HEATHROW 15 MAR 2024", "confidence": 0.85}"""

class ClaudeExtractor(BaseExtractor):
    def __init__(self, api_key: str | None = None, model: str = "claude-haiku-4-5-20251001"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def extract(self, image: np.ndarray) -> ExtractionResult:
        try:
            _, buf = cv2.imencode(".png", image)
            image_b64 = base64.standard_b64encode(buf.tobytes()).decode("utf-8")

            message = self._client.messages.create(
                model=self._model,
                max_tokens=256,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": "image/png", "data": image_b64},
                        },
                        {"type": "text", "text": _PROMPT},
                    ],
                }],
            )
            data = json.loads(message.content[0].text)
            return ExtractionResult(
                date=data.get("date"),
                country=data.get("country"),
                direction=data.get("direction"),
                raw_text=data.get("raw_text"),
                confidence=float(data.get("confidence") or 0.0),
            )
        except Exception:
            return ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)
```

- [ ] **Step 6: Run all unit tests**

```bash
pytest tests/unit/ -v
```

Expected: all tests pass, including `test_creates_claude_extractor` in `test_factory.py` which was failing before.

- [ ] **Step 7: Commit**

```bash
git add src/ocr/claude_extractor.py tests/unit/test_claude_extractor.py requirements.txt
git commit -m "feat(ocr): add ClaudeExtractor with Haiku API and mocked unit tests"
```

---

### Task 5: Public API + integration test skeleton

**Files:**
- Modify: `src/ocr/__init__.py`
- Create: `tests/integration/test_extractor_real_images.py`

**Interfaces:**
- Produces: `from src.ocr import create_extractor, ExtractionResult, BaseExtractor` works as the public import path

- [ ] **Step 1: Update `src/ocr/__init__.py`**

```python
"""OCR module — text extraction from stamp images."""

from src.ocr.base import BaseExtractor, ExtractionResult
from src.ocr.factory import create_extractor

__all__ = ["BaseExtractor", "ExtractionResult", "create_extractor"]
```

- [ ] **Step 2: Create integration test skeleton**

Create `tests/integration/test_extractor_real_images.py`:

```python
from __future__ import annotations

"""Integration tests for ClaudeExtractor with real stamp image fixtures.

All tests are skipped until stamp image fixtures are placed in
tests/fixtures/stamps/ and the skip marker is removed.

Fixture format expected:
    tests/fixtures/stamps/english_entry.png   — clear English entry stamp
    tests/fixtures/stamps/english_exit.png    — clear English exit stamp
    tests/fixtures/stamps/blurry.png          — low-quality/overlapping stamp

To unskip: remove `pytestmark = pytest.mark.skip(...)` once fixtures exist.
"""

import numpy as np
import pytest

pytestmark = pytest.mark.skip(reason="Awaiting stamp image fixtures in tests/fixtures/stamps/")


@pytest.fixture
def claude_extractor():
    from src.ocr import create_extractor
    return create_extractor("claude")  # reads ANTHROPIC_API_KEY from environment


@pytest.fixture
def english_entry_stamp():
    import cv2
    img = cv2.imread("tests/fixtures/stamps/english_entry.png")
    assert img is not None, "Place a clear English entry stamp at tests/fixtures/stamps/english_entry.png"
    return img


@pytest.fixture
def english_exit_stamp():
    import cv2
    img = cv2.imread("tests/fixtures/stamps/english_exit.png")
    assert img is not None, "Place a clear English exit stamp at tests/fixtures/stamps/english_exit.png"
    return img


@pytest.fixture
def blurry_stamp():
    import cv2
    img = cv2.imread("tests/fixtures/stamps/blurry.png")
    assert img is not None, "Place a low-quality stamp at tests/fixtures/stamps/blurry.png"
    return img


def test_legible_english_stamp_returns_date(claude_extractor, english_entry_stamp):
    from src.ocr import ExtractionResult
    result = claude_extractor.extract(english_entry_stamp)
    assert isinstance(result, ExtractionResult)
    assert result.date is not None


def test_entry_stamp_direction(claude_extractor, english_entry_stamp):
    result = claude_extractor.extract(english_entry_stamp)
    assert result.direction == "ENTRY"


def test_exit_stamp_direction(claude_extractor, english_exit_stamp):
    result = claude_extractor.extract(english_exit_stamp)
    assert result.direction == "EXIT"


def test_confidence_higher_for_clear_than_blurry(claude_extractor, english_entry_stamp, blurry_stamp):
    clear_result = claude_extractor.extract(english_entry_stamp)
    blurry_result = claude_extractor.extract(blurry_stamp)
    assert clear_result.confidence > blurry_result.confidence
```

- [ ] **Step 3: Run full test suite to confirm nothing broken**

```bash
pytest tests/unit/ -v
```

Expected: all unit tests pass. Integration tests are skipped (not failed).

- [ ] **Step 4: Commit**

```bash
git add src/ocr/__init__.py tests/integration/test_extractor_real_images.py
git commit -m "feat(ocr): export public API and add skipped integration test skeleton"
```
