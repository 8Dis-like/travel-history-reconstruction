from __future__ import annotations

"""VLM extractor using the Anthropic Claude API."""

import base64
import json
import re

import anthropic
import cv2
import numpy as np
from pydantic import BaseModel

from ocr.base import BaseExtractor, ExtractionResult

_PROMPT = """\
Analyze this passport stamp image and extract the following fields:
- date: the date in ISO 8601 format YYYY-MM-DD
- country: the ISO-3166 alpha-3 country code (e.g. GBR, USA, FRA, COL, HKG)
- direction: exactly "ENTRY" or "EXIT"
- raw_text: all visible text in the stamp exactly as it appears
- confidence: your confidence as a float 0.0-1.0

Return ONLY a JSON object with these exact keys. Set any unreadable field to null.
Example: {"date": "2024-03-15", "country": "GBR", "direction": "ENTRY", "raw_text": "HEATHROW 15 MAR 2024", "confidence": 0.85}"""


_SYSTEM_PROMPT = """
Task: Extract entry/exit stamp data from a passport page image.

BASE RATE: Most stamps you will encounter are partially illegible or 
degraded. A fully legible stamp with all three fields clearly readable 
is the exception, not the norm. The presence of visible ink does not 
mean a field is readable — smudging, overlap, low contrast, and partial 
strikes are the default condition of real stamps, not edge cases.

COST ASYMMETRY: A wrong value is far more costly than a null. Null is 
a correct, successful output — not a fallback or failure state. Guessing 
a plausible value when the evidence is ambiguous is the single worst 
outcome this task can produce, worse than returning null for every field.

APPLY FIELD RULES (evaluate each field independently — one field's clarity 
has no bearing on another):

- date: ISO 8601 (YYYY-MM-DD). Only output a date only if all three of its
  year, month, and day is legible. Otherwise, output null.
- country: ISO-3166 alpha-3 code (e.g. GBR, USA, FRA, ESP, HKG). Only 
  output a code if  you can cite what you saw (name, coat of arms, 
  unambiguous text). 
- direction: exactly "ENTRY" or "EXIT". Only output this if you can cite an 
  explicit word, arrow, or symbol. 
- confidence: 0 (nothing usable) to 1 (all visible fields fully clear). 
  If all three fields are null, confidence must be 0.

Return ONLY a JSON object with exactly these keys: date, country, 
direction, confidence. 

Example 1 — fully legible stamp:
{"date": "2024-03-15", "country": "GBR", "direction": "ENTRY", "confidence": 0.85}

Example 2 — partially legible stamp (country and direction clear, date smudged):
{"date": null, "country": "FRA", "direction": "EXIT", "confidence": 0.5}

Example 3 — partially legible stamp (date clear, country stamp too faded to read, no direction marker visible):
{"date": "2023-11-02", "country": null, "direction": null, "confidence": 0.4}

Example 4 — smudged/illegible stamp:
{"date": null, "country": null, "direction": null, "confidence": 0}

Example 5 — no stamp:
{"date": null, "country": null, "direction": null, "confidence": 0}
"""


tools = [
    {
        "name": "extract_stamp_info",
        "description": "Extract structured information from a passport stamp image.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": ["string", "null"], "description": "Date on the stamp, e.g. YYYY-MM-DD"},
                "country": {"type": ["string", "null"], "description": "Country associated with the stamp"},
                "direction": {"type": ["string", "null"], "description": "Entry or exit"},
                "confidence": {"type": "number", "description": "Confidence score between 0 and 1"},
            },
            "required": ["date", "country", "direction", "confidence"],
        },
    }
]


class LocalExtractionResult(BaseModel):
    date: str | None
    country: str | None
    direction: str | None
    confidence: float


class ClaudeExtractor(BaseExtractor):
    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        max_tokens: int = 256,
    ):
        """model is required — the pipeline supplies it from configs/pipeline.yaml
        (ocr.claude.model) via create_extractor_from_config; there is no hardcoded
        default model."""
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens


    def extract(self, image_b64_url: str) -> ExtractionResult:
        try:
            if image_b64_url.startswith("data:"):
                image_b64 = image_b64_url.split(",", 1)[1]
            else:
                image_b64 = image_b64_url

            message = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                thinking={"type": "disabled"},
                tools=tools,
                tool_choice={"type": "tool", "name": "extract_stamp_info"},
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": "image/png", "data": image_b64},
                        },
                        {"type": "text", "text": _SYSTEM_PROMPT},
                    ],
                }],
            )

            tool_use_block = next((block for block in message.content if block.type == "tool_use"), None)
            data = tool_use_block.input

            return ExtractionResult(
                date=data.get("date"),
                country=data.get("country"),
                direction=data.get("direction"),
                raw_text=None,
                confidence=float(data.get("confidence") or 0.0)
            )

        except Exception as e:
            print(f"ClaudeExtractor failed: {type(e).__name__}: {e}")
            return ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)
