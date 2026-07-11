from __future__ import annotations

"""Per-stamp-crop rotation correction.

Unlike ImageEnhancer.process() (page-level deskew via the dominant Hough-line
angle across the whole page), a single stamp printed on a passport page can be
crooked at ANY angle independent of the page's own orientation. This module
corrects a crop to upright for arbitrary input rotation, in two stages:

1. Fine angle correction: find the stamp's ink contours and use their
   combined minAreaRect to measure how far off-axis they are, then rotate to
   align them. A rectangle's minAreaRect is rotationally symmetric under
   180-degree flips, so this only removes skew -- it cannot tell "upright"
   from "upside down" (or "sideways").
2. Orientation disambiguation: brute-force score the four 90-degree-aligned
   orientations of the fine-corrected crop by horizontal text-line density
   and keep the best one, resolving the 90/180/270 ambiguity step 1 leaves
   behind.

Together these handle any input rotation angle, not just small skew.
"""

import cv2
import numpy as np

_INK_LOWER_BLUE = (90, 40, 40)
_INK_UPPER_BLUE = (140, 255, 255)
_INK_LOWER_RED1 = (0, 50, 50)
_INK_UPPER_RED1 = (10, 255, 255)
_INK_LOWER_RED2 = (160, 50, 50)
_INK_UPPER_RED2 = (180, 255, 255)
_INK_DARK_MAX = 80
_MIN_INK_AREA = 40


def _ink_mask(image: np.ndarray) -> np.ndarray:
    """Same blue/red/dark ink segmentation used by MockStampDetector."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blue = cv2.inRange(hsv, _INK_LOWER_BLUE, _INK_UPPER_BLUE)
    red = cv2.inRange(hsv, _INK_LOWER_RED1, _INK_UPPER_RED1) | cv2.inRange(
        hsv, _INK_LOWER_RED2, _INK_UPPER_RED2
    )
    dark = cv2.inRange(gray, 0, _INK_DARK_MAX)

    combined = blue | red | dark
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    return cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)


def _rotate_expand(image: np.ndarray, angle_deg: float) -> np.ndarray:
    """Rotate around center by an arbitrary angle, expanding the canvas so
    nothing gets cropped off. Used for the fine (sub-90-degree) correction."""
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
        image,
        matrix,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )


def _rotate_90_multiple(image: np.ndarray, degrees: int) -> np.ndarray:
    """Exact, lossless rotation for 0/90/180/270 (no interpolation needed)."""
    if degrees == 90:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if degrees == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    if degrees == 270:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    return image


def estimate_skew_angle(image: np.ndarray) -> float:
    """Angle (degrees) the stamp's ink is off-axis, normalized to (-45, 45].

    Returns 0.0 if no ink contours are found (e.g. blank crop).
    """
    mask = _ink_mask(image)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) >= _MIN_INK_AREA]
    if not contours:
        return 0.0

    # Union of all ink points, not just the largest fragment -- stamp ink is
    # often fragmented into several contours (text, emblem, border).
    all_points = np.vstack(contours)
    rect = cv2.minAreaRect(all_points)
    angle = rect[-1]

    # OpenCV's minAreaRect angle convention varies by rectangle orientation;
    # normalize to (-45, 45] regardless of which OpenCV version/edge case.
    if angle < -45:
        angle += 90
    elif angle > 45:
        angle -= 90
    return float(angle)


def _horizontal_line_score(image: np.ndarray) -> float:
    """Higher = more horizontal text-like edges = more likely this
    orientation is upright. Same heuristic as ImageEnhancer._auto_orient,
    reimplemented here to keep this module independent (crop-level, not
    page-level; different owner/scope)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=30, minLineLength=20, maxLineGap=8
    )
    if lines is None:
        return 0.0

    score = 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        line_angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if line_angle < 15 or line_angle > 165:
            score += 1
    return float(score)


def deskew_stamp_crop(crop: np.ndarray) -> tuple[np.ndarray, float]:
    """Correct an arbitrarily-rotated stamp crop to upright.

    Handles any input angle: first removes continuous skew via the ink
    contours' combined minAreaRect, then disambiguates the remaining
    90-degree-grid ambiguity (including a full 180-degree flip, or a
    90-degree sideways rotation) by picking whichever of the four
    grid-aligned orientations has the most horizontal text-like edges.

    Args:
        crop: BGR stamp crop, e.g. straight from StampDetection.crop.

    Returns:
        (corrected_image, total_rotation_applied_degrees). The angle is
        informational only (for logging), not required by callers.
    """
    skew_angle = estimate_skew_angle(crop)
    fine_aligned = crop if skew_angle == 0.0 else _rotate_expand(crop, skew_angle)

    best_image = fine_aligned
    best_score = -1.0
    best_extra_rotation = 0

    for extra_rotation in (0, 90, 180, 270):
        candidate = _rotate_90_multiple(fine_aligned, extra_rotation)
        score = _horizontal_line_score(candidate)
        if score > best_score:
            best_score = score
            best_image = candidate
            best_extra_rotation = extra_rotation

    total_rotation = skew_angle + best_extra_rotation
    return best_image, total_rotation
