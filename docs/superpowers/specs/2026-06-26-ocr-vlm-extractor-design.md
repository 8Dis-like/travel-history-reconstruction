# OCR/VLM Extractor Design

**Date:** 2026-06-26  
**Owner:** Zuyan Tao  
**Stage:** Stage 2–3 (Date Extraction → Full Field Extraction)

---

## 1. Problem

The pipeline receives cropped stamp images (numpy arrays) from Hao's detection module and needs to extract structured fields: date, country, direction. The extraction must be multilingual-ready and support swapping providers without changing downstream code.

## 2. Approach

Use a VLM-only extraction strategy (no traditional OCR layer). Traditional OCR requires per-language model configuration and degrades on degraded/overlapping stamps. VLMs handle multilingual and low-quality images naturally.

Apply the factory pattern with an ABC base class so the pipeline always talks to one interface regardless of which provider is active.

## 3. Module Structure

```
src/ocr/
├── __init__.py
├── base.py              # BaseExtractor ABC + ExtractionResult dataclass
├── factory.py           # create_extractor(provider, **kwargs) → BaseExtractor
├── claude_extractor.py  # ClaudeExtractor — claude-haiku-4-5 via Anthropic API
└── local_extractor.py   # LocalVLMExtractor — stub only, raises NotImplementedError
```

## 4. Data Contract

```python
@dataclass
class ExtractionResult:
    date: str | None       # ISO 8601 format: "2024-03-15", None if unreadable
    country: str | None    # ISO-3166 alpha-3: "GBR", None if unreadable
    direction: str | None  # "ENTRY" or "EXIT", None if unreadable
    raw_text: str | None   # Raw text as seen in the stamp
    confidence: float      # 0.0–1.0, model's self-reported confidence
```

All fields except `confidence` can be `None` — an unreadable stamp is a valid result, not an error.

## 5. Interface

```python
class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, image: np.ndarray) -> ExtractionResult:
        """Extract structured fields from a stamp crop.

        Args:
            image: BGR numpy array (H, W, 3), directly from detection crop.

        Returns:
            ExtractionResult with any unreadable fields set to None.
        """
```

The `image` parameter matches the `det.crop` format already defined in `StampDetection` (see `src/detection/stamp_detector.py`), so no format conversion is needed at the docking point.

## 6. ClaudeExtractor

- Model: `claude-haiku-4-5-20251001`
- Encodes the numpy array to base64 PNG in memory (no disk I/O)
- Sends a structured prompt asking for JSON output with the four fields
- Parses the JSON response into `ExtractionResult`
- On API error or malformed JSON: returns `ExtractionResult` with all fields `None` and `confidence=0.0` (does not raise — the pipeline flags low-confidence results downstream)

## 7. LocalVLMExtractor

Stub only. Implements the ABC so it can be instantiated and passed around, but `extract()` raises `NotImplementedError`. Exists so the factory and config system work end-to-end without the local model weights present.

## 8. Factory

```python
def create_extractor(provider: str, **kwargs) -> BaseExtractor:
    """
    provider: "claude" | "local"
    kwargs: passed to the provider constructor (e.g., api_key, model)
    """
```

Raises `ValueError` for unknown providers.

## 9. Test Plan (TDD)

Tests are written before implementation. Real stamp image tests are deferred until test fixtures are available.

### Unit tests (no images needed)

**`tests/unit/test_factory.py`**
- `create_extractor("claude")` returns a `ClaudeExtractor` instance
- `create_extractor("local")` returns a `LocalVLMExtractor` instance
- `create_extractor("unknown")` raises `ValueError`
- Both returned instances are subclasses of `BaseExtractor`

**`tests/unit/test_claude_extractor.py`** (Anthropic client mocked)
- Valid API JSON response → correct `ExtractionResult` fields
- API response with missing fields → those fields are `None`
- API error (network/auth) → returns all-None `ExtractionResult`, confidence=0.0, does not raise
- Malformed JSON in API response → returns all-None `ExtractionResult`, does not raise

**`tests/unit/test_interface_contract.py`**
- `BaseExtractor` cannot be instantiated directly (raises `TypeError`)
- `ClaudeExtractor` and `LocalVLMExtractor` both satisfy the ABC (can be instantiated)
- `extract()` accepts a 3D uint8 numpy array
- `extract()` return type is `ExtractionResult`
- `LocalVLMExtractor.extract()` raises `NotImplementedError`

### Integration tests (deferred — awaiting stamp image fixtures)

**`tests/integration/test_extractor_real_images.py`**
- Real stamp crop → non-None date on legible English stamps
- Real stamp crop → correct direction ("ENTRY"/"EXIT") on stamps with clear indicators
- Confidence score reflects legibility (low confidence on blurry/overlapping stamps)

## 10. Out of Scope

- Field parsing / regex post-processing (`field_parser.py`) — separate module, separate spec
- Timeline reconstruction — separate module
- FastAPI endpoints — separate spec
- Prompt engineering iteration — implementation concern, not a design decision
