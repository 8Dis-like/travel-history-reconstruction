from __future__ import annotations

"""
Mock Stamp Detector — Contour-based stamp region extraction.

This module provides a TEMPORARY, training-free stamp detector that uses
classical CV (color filtering + contour detection) to extract stamp-like
regions from passport pages. It outputs the EXACT same StampDetection /
DetectionResult dataclasses as the real YOLOv8 StampDetector, so
downstream code (OCR, extraction, timeline) works identically.

Purpose:
    Let Zuyan (OCR/backend) and Wilson (frontend) develop and test their
    modules RIGHT NOW without waiting for Hao's fine-tuned best.pt.

    When best.pt is ready, just swap:
        detector = MockStampDetector()      # ← remove this
        detector = StampDetector("best.pt") # ← use this
    Zero downstream code changes needed.

Owner: Hao Zhang
"""

import cv2
import time
import numpy as np
from pathlib import Path
from typing import Optional

from src.detection.stamp_detector import StampDetection, DetectionResult


class MockStampDetector:
    """Contour-based mock detector — same interface as StampDetector.

    Uses color segmentation in HSV space to find ink-colored regions
    (blue, red, purple, black stamps) and returns them as StampDetection
    objects with crops. Not accurate enough for production, but gives
    real stamp-like crops for OCR development.

    Usage:
        from src.detection.mock_detector import MockStampDetector
        detector = MockStampDetector()
        result = detector.detect("data/processed/enhanced/enhanced_page_001.png")
        for det in result.detections:
            print(f"{det.stamp_id}: bbox={det.bbox_xyxy}, conf={det.confidence:.2f}")
            # det.crop is a numpy array ready for OCR
    """

    def __init__(
        self,
        min_stamp_area: int = 5000,
        max_stamp_area: int = 500000,
        min_aspect_ratio: float = 0.3,
        max_aspect_ratio: float = 3.0,
        merge_distance: int = 30,
        padding: int = 15,
    ):
        """Initialize the mock detector.

        Args:
            min_stamp_area: Minimum contour area (pixels²) to consider.
            max_stamp_area: Maximum contour area to avoid page-level detections.
            min_aspect_ratio: Min width/height ratio (filters out thin lines).
            max_aspect_ratio: Max width/height ratio.
            merge_distance: Merge bounding boxes within this pixel distance.
            padding: Extra pixels around each crop for OCR context.
        """
        self.min_stamp_area = min_stamp_area
        self.max_stamp_area = max_stamp_area
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.merge_distance = merge_distance
        self.padding = padding

    def detect(
        self,
        image: str | Path | np.ndarray,
        extract_crops: bool = True,
        source_name: Optional[str] = None,
    ) -> DetectionResult:
        """Run mock stamp detection on a single image.

        Returns the same DetectionResult as StampDetector.detect().
        """
        t0 = time.time()

        # Load image
        if isinstance(image, (str, Path)):
            source_name = source_name or Path(image).name
            img_bgr = cv2.imread(str(image))
            if img_bgr is None:
                raise FileNotFoundError(f"Cannot read image: {image}")
        else:
            source_name = source_name or "array_input"
            img_bgr = image

        h, w = img_bgr.shape[:2]

        # --- Core detection: color-based segmentation ---
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # Mask 1: Blue/purple ink stamps (common for entry stamps)
        blue_mask = cv2.inRange(hsv, (90, 40, 40), (140, 255, 255))

        # Mask 2: Red ink stamps (common for exit stamps)
        red_lower = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
        red_upper = cv2.inRange(hsv, (160, 50, 50), (180, 255, 255))
        red_mask = red_lower | red_upper

        # Mask 3: Dark ink (black stamps, dark text)
        dark_mask = cv2.inRange(gray, 0, 80)
        # Exclude very large dark areas (page borders, shadows)
        dark_mask = cv2.morphologyEx(
            dark_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)
        )

        # Combine all ink masks
        combined = blue_mask | red_mask | dark_mask

        # Morphological cleanup: close gaps within stamps
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

        # Find contours
        contours, _ = cv2.findContours(
            combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter contours by area and aspect ratio
        raw_boxes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_stamp_area or area > self.max_stamp_area:
                continue

            x, y, bw, bh = cv2.boundingRect(contour)
            aspect = bw / max(bh, 1)
            if aspect < self.min_aspect_ratio or aspect > self.max_aspect_ratio:
                continue

            raw_boxes.append((x, y, x + bw, y + bh, area))

        # Merge nearby boxes (stamps often fragment into multiple contours)
        merged_boxes = self._merge_boxes(raw_boxes)

        # Build StampDetection objects
        detections = []
        for i, (x1, y1, x2, y2) in enumerate(merged_boxes):
            crop = None
            if extract_crops:
                cx1 = max(0, x1 - self.padding)
                cy1 = max(0, y1 - self.padding)
                cx2 = min(w, x2 + self.padding)
                cy2 = min(h, y2 + self.padding)
                crop = img_bgr[cy1:cy2, cx1:cx2].copy()

            # Confidence heuristic: based on how "stamp-shaped" the region is
            box_area = (x2 - x1) * (y2 - y1)
            confidence = min(0.95, max(0.30, box_area / 50000))

            det = StampDetection(
                stamp_id=f"MOCK_{i+1:03d}",
                bbox_xyxy=(x1, y1, x2, y2),
                confidence=confidence,
                class_name="stamp_mock",
                crop=crop,
            )
            detections.append(det)

        # Sort by y-coordinate (top to bottom), then x (left to right)
        detections.sort(key=lambda d: (d.bbox_xyxy[1], d.bbox_xyxy[0]))

        # Re-number after sorting
        for i, det in enumerate(detections):
            det.stamp_id = f"MOCK_{i+1:03d}"

        elapsed_ms = (time.time() - t0) * 1000

        return DetectionResult(
            source_image=source_name,
            image_shape=(h, w),
            detections=detections,
            inference_time_ms=elapsed_ms,
        )

    def detect_batch(
        self,
        image_paths: list[str | Path],
        extract_crops: bool = True,
    ) -> list[DetectionResult]:
        """Run detection on multiple images."""
        return [self.detect(p, extract_crops=extract_crops) for p in image_paths]

    def save_crops(
        self,
        result: DetectionResult,
        output_dir: str | Path,
        prefix: Optional[str] = None,
    ) -> list[Path]:
        """Save cropped stamp images to disk (same interface as StampDetector)."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if prefix is None:
            prefix = Path(result.source_image).stem

        saved_paths = []
        for det in result.detections:
            if det.crop is None:
                continue
            filename = f"{prefix}_{det.stamp_id}.jpg"
            save_path = output_dir / filename
            cv2.imwrite(str(save_path), det.crop)
            saved_paths.append(save_path)

        return saved_paths

    def visualize(
        self,
        image: np.ndarray,
        result: DetectionResult,
        show_labels: bool = True,
        line_thickness: int = 2,
    ) -> np.ndarray:
        """Draw detection boxes — same interface as StampDetector.visualize()."""
        annotated = image.copy()
        for det in result.detections:
            x1, y1, x2, y2 = det.bbox_xyxy
            color = (255, 165, 0)  # Orange for mock detections

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, line_thickness)

            if show_labels:
                label = f"{det.stamp_id} {det.confidence:.0%}"
                font_scale = 0.6
                thickness = 1
                (tw, th), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
                )
                cv2.rectangle(
                    annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1
                )
                cv2.putText(
                    annotated, label, (x1 + 2, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness,
                )

        return annotated

    def _merge_boxes(
        self, boxes: list[tuple[int, int, int, int, int]]
    ) -> list[tuple[int, int, int, int]]:
        """Merge overlapping or nearby bounding boxes."""
        if not boxes:
            return []

        # Sort by x1
        boxes = sorted(boxes, key=lambda b: b[0])
        merged = []

        for x1, y1, x2, y2, _ in boxes:
            if not merged:
                merged.append([x1, y1, x2, y2])
                continue

            # Check if this box overlaps or is close to the last merged box
            lx1, ly1, lx2, ly2 = merged[-1]
            if (x1 <= lx2 + self.merge_distance and
                y1 <= ly2 + self.merge_distance and
                y2 >= ly1 - self.merge_distance):
                # Merge
                merged[-1] = [
                    min(lx1, x1), min(ly1, y1),
                    max(lx2, x2), max(ly2, y2),
                ]
            else:
                merged.append([x1, y1, x2, y2])

        return [tuple(b) for b in merged]
