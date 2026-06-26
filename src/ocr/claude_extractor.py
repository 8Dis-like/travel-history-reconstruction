from __future__ import annotations

"""VLM extractor using the Anthropic Claude API."""

import base64
import json

import anthropic
import cv2
import numpy as np

from src.ocr.base import BaseExtractor, ExtractionResult

_PROMPT = """\
Analyze this passport stamp image and extract the following fields:
- date: the date in ISO 8601 format YYYY-MM-DD
- country: the ISO-3166 alpha-3 country code (e.g. GBR, USA, FRA, COL, HKG)
- direction: exactly "ENTRY" or "EXIT"
- raw_text: all visible text in the stamp exactly as it appears
- confidence: your confidence as a float 0.0-1.0

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
