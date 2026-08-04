from __future__ import annotations

"""Local VLM extractor using Qwen2-VL."""

import json
import re
import cv2
import numpy as np
from PIL import Image

try:
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from qwen_vl_utils import process_vision_info
except ImportError:
    torch, Qwen2VLForConditionalGeneration, AutoProcessor, process_vision_info = None, None, None, None

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


class LocalVLMExtractor(BaseExtractor):
    def __init__(self, model: str = "Qwen/Qwen2-VL-2B-Instruct", cache_dir: str = "models", **kwargs):
        if Qwen2VLForConditionalGeneration is None:
            print("Warning: 'transformers' and 'qwen-vl-utils' are required. Run `pip install transformers qwen-vl-utils torchvision`.")
            self._model = None
            self._processor = None
            return
            
        print(f"Loading local VLM model '{model}' into '{cache_dir}'...")
        
        # Load model and processor locally
        self._model = Qwen2VLForConditionalGeneration.from_pretrained(
            model,
            torch_dtype="auto",
            device_map="auto",
            cache_dir=cache_dir
        )
        self._processor = AutoProcessor.from_pretrained(
            model,
            cache_dir=cache_dir
        )

    def extract(self, image: np.ndarray) -> ExtractionResult:
        if self._model is None or self._processor is None:
            return ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)

        try:
            # Convert OpenCV BGR to RGB, then to PIL Image
            rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)

            # Build messages for Qwen2-VL
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": pil_img},
                        {"type": "text", "text": _PROMPT}
                    ]
                }
            ]
            
            # Prepare inputs using Qwen's chat template
            text = self._processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            
            inputs = self._processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            )
            
            # Move inputs to same device as model
            inputs = inputs.to(self._model.device)
            
            # Generate output
            generated_ids = self._model.generate(**inputs, max_new_tokens=256)
            
            # Trim the prompt from the generated ids
            generated_ids_trimmed = [
                out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            
            output_text = self._processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
            
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", output_text.strip())
            data = json.loads(raw)
            return ExtractionResult(
                date=data.get("date"),
                country=data.get("country"),
                direction=data.get("direction"),
                raw_text=data.get("raw_text"),
                confidence=float(data.get("confidence") or 0.0),
            )
        except Exception as e:
            print(f"Local OCR Error: {e}")
            return ExtractionResult(date=None, country=None, direction=None, raw_text=None, confidence=0.0)
