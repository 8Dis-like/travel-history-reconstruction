"""
Image Enhancement Pipeline for Passport Page Preprocessing.

This module handles deskewing, denoising, and contrast enhancement
to prepare scanned passport images for stamp detection.

Owner: Hao Zhang
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional


class ImageEnhancer:
    """Preprocesses scanned passport page images for downstream detection."""

    def __init__(
        self,
        target_dpi: int = 300,
        denoise: bool = True,
        deskew: bool = True,
        contrast_enhance: bool = True,
        max_image_size: int = 4096,
    ):
        self.target_dpi = target_dpi
        self.denoise = denoise
        self.deskew = deskew
        self.contrast_enhance = contrast_enhance
        self.max_image_size = max_image_size

    def process(self, image: np.ndarray) -> np.ndarray:
        """Run the full enhancement pipeline on a single image.

        Args:
            image: BGR image as numpy array (OpenCV format).

        Returns:
            Enhanced BGR image as numpy array.
        """
        img = image.copy()

        # Step 1: Resize if exceeding max dimension
        img = self._resize_if_needed(img)

        # Step 2: Deskew (correct rotation)
        if self.deskew:
            img = self._deskew(img)

        # Step 3: Denoise
        if self.denoise:
            img = self._denoise(img)

        # Step 4: Contrast enhancement via CLAHE
        if self.contrast_enhance:
            img = self._enhance_contrast(img)

        return img

    def process_file(
        self, input_path: str | Path, output_path: Optional[str | Path] = None
    ) -> np.ndarray:
        """Load an image file, process it, and optionally save the result.

        Args:
            input_path: Path to the input image.
            output_path: If provided, save the enhanced image here.

        Returns:
            Enhanced BGR image as numpy array.
        """
        img = cv2.imread(str(input_path))
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {input_path}")

        enhanced = self.process(img)

        if output_path is not None:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), enhanced)

        return enhanced

    # ------------------------------------------------------------------ #
    #  Private helpers
    # ------------------------------------------------------------------ #

    def _resize_if_needed(self, img: np.ndarray) -> np.ndarray:
        """Downscale if any dimension exceeds max_image_size."""
        h, w = img.shape[:2]
        if max(h, w) <= self.max_image_size:
            return img
        scale = self.max_image_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def _deskew(self, img: np.ndarray) -> np.ndarray:
        """Correct small rotations using Hough line detection."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10
        )
        if lines is None:
            return img

        # Compute median angle of detected lines
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            angles.append(angle)

        median_angle = np.median(angles)

        # Only correct if the skew is small (< 15 degrees)
        if abs(median_angle) > 15:
            return img

        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            img, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated

    def _denoise(self, img: np.ndarray) -> np.ndarray:
        """Apply non-local means denoising."""
        return cv2.fastNlMeansDenoisingColored(img, None, h=6, hForColorComponents=6)

    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)

        lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
