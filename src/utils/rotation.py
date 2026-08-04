from __future__ import annotations

"""Shared image rotation helper used by the rotation-robustness tooling."""

import cv2
import numpy as np


def rotate_image(image: np.ndarray, angle_deg: float) -> np.ndarray:
    """Rotate around center, expanding the canvas so nothing gets cropped.

    Empty corners are filled with white to match the stamp crops (which are
    flattened onto white), so rotation adds no spurious dark background.
    """
    h, w = image.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)

    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)

    matrix[0, 2] += (new_w - w) / 2
    matrix[1, 2] += (new_h - h) / 2

    return cv2.warpAffine(
        image, matrix, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255)
    )
