from __future__ import annotations

"""VLM extractor using the DeepSeek API."""

import base64
import json
import re
import cv2
import numpy as np

# We use the openai python client since DeepSeek provides an OpenAI-compatible API
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

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

import os
class DeepseekExtractor(BaseExtractor):
    def __init__(self, api_key: str | None = None, model: str = "deepseek-chat"):
        if OpenAI is None:
            print("Warning: 'openai' package is required for DeepseekExtractor. Run `pip install openai`.")
            self._client = None
        else:
            try:
                actual_key = api_key or os.getenv("DEEPSEEK_API_KEY")
                self._client = OpenAI(
                    api_key=actual_key,
                    base_url="https://api.deepseek.com/v1"
                )
            except Exception as e:
                print(f"Warning: Failed to initialize DeepSeek client (Missing API Key?). OCR will return None. Details: {e}")
                self._client = None
        self._model = model

    def extract(self, image: np.ndarray) -> ExtractionResult:
        if self._client is None:
            return ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)
            
        try:
            _, buf = cv2.imencode(".png", image)
            image_b64 = base64.standard_b64encode(buf.tobytes()).decode("utf-8")

            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _PROMPT},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                        ]
                    }
                ],
                max_tokens=256
            )
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.choices[0].message.content.strip())
            data = json.loads(raw)
            return ExtractionResult(
                date=data.get("date"),
                country=data.get("country"),
                direction=data.get("direction"),
                raw_text=data.get("raw_text"),
                confidence=float(data.get("confidence") or 0.0),
            )
        except Exception as e:
            print(f"DeepSeek OCR Error: {e}")
            return ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)
