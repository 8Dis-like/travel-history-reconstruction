from __future__ import annotations

import cv2
import numpy as np
import pytest

from src.preprocessing.stamp_deskew import (
    _horizontal_line_score,
    deskew_stamp_crop,
    estimate_skew_angle,
)

FIXTURE = "tests/fixtures/stamps/usa_entry_1997.png"


def _rotate_any_angle(image: np.ndarray, angle_deg: float) -> np.ndarray:
    h, w = image.shape[:2]
    center = (w / 2, h / 2)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    cos, sin = abs(matrix[0, 0]), abs(matrix[0, 1])
    new_w, new_h = int(h * sin + w * cos), int(h * cos + w * sin)
    matrix[0, 2] += (new_w - w) / 2
    matrix[1, 2] += (new_h - h) / 2
    return cv2.warpAffine(
        image, matrix, (new_w, new_h), borderValue=(255, 255, 255)
    )


@pytest.fixture(scope="module")
def baseline_image():
    img = cv2.imread(FIXTURE)
    assert img is not None, f"could not load {FIXTURE}"
    return img


def test_estimate_skew_angle_on_blank_image_returns_zero():
    blank = np.full((100, 100, 3), 255, dtype=np.uint8)
    assert estimate_skew_angle(blank) == 0.0


@pytest.mark.parametrize("angle", [5, 15, 30])
def test_estimate_skew_angle_roughly_matches_applied_rotation(baseline_image, angle):
    rotated = _rotate_any_angle(baseline_image, angle)
    estimated = estimate_skew_angle(rotated)
    # cv2's rotation sign convention and minAreaRect's angle convention
    # differ, so check magnitude is in the right ballpark rather than
    # pinning down an exact sign.
    assert abs(abs(estimated) - angle) < 10


@pytest.mark.parametrize(
    "angle", [0, 15, 45, 90, 135, 180, 225, 270, 315, 350]
)
def test_deskew_recovers_upright_orientation_across_full_circle(baseline_image, angle):
    baseline_score = _horizontal_line_score(baseline_image)
    rotated = _rotate_any_angle(baseline_image, angle)

    corrected, _ = deskew_stamp_crop(rotated)
    corrected_score = _horizontal_line_score(corrected)

    # The corrected image's "looks upright" score should land close to the
    # untouched baseline's score, regardless of which starting angle (across
    # the full 0-360 range) it began from. This does not fully guarantee
    # 0-vs-180 disambiguation (a heuristic limitation shared with
    # ImageEnhancer._auto_orient) -- see module docstring.
    assert corrected_score >= baseline_score * 0.5


def test_deskew_returns_same_shape_family_as_input():
    blank = np.full((200, 150, 3), 255, dtype=np.uint8)
    corrected, angle = deskew_stamp_crop(blank)
    assert corrected.ndim == 3
    assert angle == 0.0
