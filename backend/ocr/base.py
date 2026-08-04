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
