from __future__ import annotations

"""
Image Enhancement Pipeline for Passport Page Preprocessing.

This module handles orientation correction, deskewing, denoising,
and contrast enhancement to prepare scanned passport images for
stamp detection.

Owner: Hao Zhang
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class EnhancementReport:
    """Summary of what the enhancer did to an image."""
    original_shape: tuple[int, int]
    final_shape: tuple[int, int]
    was_resized: bool
    rotation_applied_deg: float
    deskew_angle_deg: float
    denoise_applied: bool
    contrast_enhanced: bool

    def __str__(self) -> str:
        lines = [
            f"Original: {self.original_shape[1]}x{self.original_shape[0]}",
            f"Final:    {self.final_shape[1]}x{self.final_shape[0]}",
            f"Resized:  {self.was_resized}",
            f"Rotation: {self.rotation_applied_deg:.1f}°",
            f"Deskew:   {self.deskew_angle_deg:.2f}°",
            f"Denoise:  {self.denoise_applied}",
            f"CLAHE:    {self.contrast_enhanced}",
        ]
        return " | ".join(lines)


class ImageEnhancer:
    """Preprocesses scanned passport page images for downstream detection."""

    def __init__(
        self,
        target_dpi: int = 300,
        denoise: bool = True,
        deskew: bool = True,
        auto_orient: bool = True,
        contrast_enhance: bool = True,
        max_image_size: int = 4096,
    ):
        self.target_dpi = target_dpi
        self.denoise = denoise
        self.deskew = deskew
        self.auto_orient = auto_orient
        self.contrast_enhance = contrast_enhance
        self.max_image_size = max_image_size

    def process(self, image: np.ndarray) -> tuple[np.ndarray, EnhancementReport]:
        """Run the full enhancement pipeline on a single image.

        Args:
            image: BGR image as numpy array (OpenCV format).

        Returns:
            Tuple of (enhanced BGR image, EnhancementReport).
        """
        img = image.copy()
        original_shape = img.shape[:2]
        rotation_applied = 0.0
        deskew_angle = 0.0

        # Step 1: Resize if exceeding max dimension
        img, was_resized = self._resize_if_needed(img)

        # Step 2: Auto-orient (correct 90/180/270 degree rotations)
        if self.auto_orient:
            img, rotation_applied = self._auto_orient(img)

        # Step 3: Fine deskew (correct small rotation angles)
        if self.deskew:
            img, deskew_angle = self._deskew(img)

        # Step 4: Denoise
        if self.denoise:
            img = self._denoise(img)

        # Step 5: Contrast enhancement via CLAHE
        if self.contrast_enhance:
            img = self._enhance_contrast(img)

        report = EnhancementReport(
            original_shape=original_shape,
            final_shape=img.shape[:2],
            was_resized=was_resized,
            rotation_applied_deg=rotation_applied,
            deskew_angle_deg=deskew_angle,
            denoise_applied=self.denoise,
            contrast_enhanced=self.contrast_enhance,
        )
        return img, report

    def process_file(
        self, input_path: str | Path, output_path: Optional[str | Path] = None
    ) -> tuple[np.ndarray, EnhancementReport]:
        """Load an image file, process it, and optionally save the result.

        Args:
            input_path: Path to the input image.
            output_path: If provided, save the enhanced image here.

        Returns:
            Tuple of (enhanced BGR image, EnhancementReport).
        """
        img = cv2.imread(str(input_path))
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {input_path}")

        enhanced, report = self.process(img)

        if output_path is not None:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), enhanced)

        return enhanced, report

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    def _resize_if_needed(self, img: np.ndarray) -> tuple[np.ndarray, bool]:
        """Downscale if any dimension exceeds max_image_size."""
        h, w = img.shape[:2]
        if max(h, w) <= self.max_image_size:
            return img, False
        scale = self.max_image_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA), True

    def _auto_orient(self, img: np.ndarray) -> tuple[np.ndarray, float]:
        """Detect and correct 90/180/270 degree rotations.

        Uses edge/text line analysis to find the dominant orientation.
        Passport pages are typically portrait (height > width), and text
        lines should be roughly horizontal in the correct orientation.
        """
        h, w = img.shape[:2]

        # Test all 4 orientations and score each by horizontal text line density
        best_score = -1
        best_rotation = 0

        for rotation_deg in [0, 90, 180, 270]:
            rotated = self._rotate_90_multiples(img, rotation_deg)
            score = self._horizontal_line_score(rotated)
            if score > best_score:
                best_score = score
                best_rotation = rotation_deg

        if best_rotation == 0:
            return img, 0.0

        return self._rotate_90_multiples(img, best_rotation), float(best_rotation)

    @staticmethod
    def _rotate_90_multiples(img: np.ndarray, degrees: int) -> np.ndarray:
        """Efficiently rotate by exact 90-degree multiples using numpy."""
        if degrees == 0:
            return img
        elif degrees == 90:
            return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif degrees == 180:
            return cv2.rotate(img, cv2.ROTATE_180)
        elif degrees == 270:
            return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        return img

    @staticmethod
    def _horizontal_line_score(img: np.ndarray) -> float:
        """Score how many horizontal text-like edges exist in this orientation.

        Higher score = more horizontal lines = more likely correct orientation.
        """
        # Downscale for speed
        h, w = img.shape[:2]
        scale = 800 / max(h, w)
        small = cv2.resize(img, (int(w * scale), int(h * scale)),
                           interpolation=cv2.INTER_AREA)

        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=50,
            minLineLength=40, maxLineGap=10
        )
        if lines is None:
            return 0.0

        lines = lines.reshape(-1, 4)
        horizontal_count = 0
        for x1, y1, x2, y2 in lines:
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            # Count lines within ±15° of horizontal
            if angle < 15 or angle > 165:
                horizontal_count += 1

        return horizontal_count

    def _deskew(self, img: np.ndarray) -> tuple[np.ndarray, float]:
        """Correct small rotations using Hough line detection."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10
        )
        if lines is None:
            return img, 0.0

        lines = lines.reshape(-1, 4)
        # Compute median angle of near-horizontal lines
        angles = []
        for x1, y1, x2, y2 in lines:
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Only consider near-horizontal lines for deskew
            if abs(angle) < 30:
                angles.append(angle)

        if len(angles) == 0:
            return img, 0.0

        median_angle = np.median(angles)

        # Only correct if the skew is small (< 10 degrees)
        if abs(median_angle) > 10 or abs(median_angle) < 0.3:
            return img, 0.0

        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            img, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated, median_angle

    def _denoise(self, img: np.ndarray) -> np.ndarray:
        """Apply non-local means denoising."""
        return cv2.fastNlMeansDenoisingColored(img, None, h=6, hColor=6)

    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)

        lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

