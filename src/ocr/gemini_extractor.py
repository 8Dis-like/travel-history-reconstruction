from __future__ import annotations

"""VLM extractor using Google Gemini API."""

import json
import re
import cv2
import numpy as np

try:
    import google.generativeai as genai
except ImportError:
    genai = None

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

class GeminiExtractor(BaseExtractor):
    def __init__(self, api_key: str | None = None, model: str = "gemini-3.5-flash"):
        import os
        if genai is None:
            print("Warning: 'google-generativeai' package is required for GeminiExtractor. Run `pip install google-generativeai`.")
            self._model = None
        else:
            actual_key = api_key or os.getenv("GEMINI_API_KEY")
            if not actual_key:
                print("Warning: GEMINI_API_KEY is not set.")
                self._model = None
            else:
                genai.configure(api_key=actual_key)
                self._model = genai.GenerativeModel(model)

    def extract(self, image: np.ndarray) -> ExtractionResult:
        if self._model is None:
            return ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)
            
        try:
            # Convert OpenCV BGR to RGB, then to PIL Image for Gemini
            from PIL import Image
            rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)

            response = self._model.generate_content([_PROMPT, pil_img])
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.text.strip())
            data = json.loads(raw)
            
            return ExtractionResult(
                date=data.get("date"),
                country=data.get("country"),
                direction=data.get("direction"),
                raw_text=data.get("raw_text"),
                confidence=float(data.get("confidence") or 0.0),
            )
        except Exception as e:
            print(f"Gemini OCR Error: {e}")
            return ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)
