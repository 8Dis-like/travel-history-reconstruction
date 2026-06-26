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
