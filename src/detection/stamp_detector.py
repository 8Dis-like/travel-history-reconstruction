from __future__ import annotations

"""
Stamp Detector — YOLOv8 wrapper for passport stamp localization.

Provides a clean interface to:
  1. Load a pretrained or fine-tuned YOLOv8 model
  2. Run inference on single images or batches
  3. Return structured detection results with bounding boxes and crops

Owner: Hao Zhang
"""

import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from ultralytics import YOLO


# ------------------------------------------------------------------ #
#  Data classes for structured output
# ------------------------------------------------------------------ #

@dataclass
class StampDetection:
    """A single detected stamp region."""
    stamp_id: str
    bbox_xyxy: tuple[int, int, int, int]   # (x1, y1, x2, y2) absolute coords
    confidence: float
    class_name: str
    crop: Optional[np.ndarray] = field(default=None, repr=False)

    @property
    def bbox_xywh(self) -> tuple[int, int, int, int]:
        """Convert xyxy to xywh format."""
        x1, y1, x2, y2 = self.bbox_xyxy
        return (x1, y1, x2 - x1, y2 - y1)


@dataclass
class DetectionResult:
    """Result of running stamp detection on a single image."""
    source_image: str
    image_shape: tuple[int, int]            # (height, width)
    detections: list[StampDetection]
    inference_time_ms: float

    @property
    def count(self) -> int:
        return len(self.detections)


# ------------------------------------------------------------------ #
#  Main detector class
# ------------------------------------------------------------------ #

class StampDetector:
    """YOLOv8-based passport stamp detector.

    Usage:
        detector = StampDetector("models/finetuned/stamp_yolov8s.pt")
        result = detector.detect("passport_page.jpg")
        for det in result.detections:
            print(f"Stamp {det.stamp_id}: conf={det.confidence:.2f}")
    """

    def __init__(
        self,
        model_path: str = "yolov8s.pt",
        confidence_threshold: float = 0.4,
        iou_threshold: float = 0.45,
        device: Optional[str] = None,
        imgsz: int = 640,
    ):
        """Initialize the stamp detector.

        Args:
            model_path: Path to YOLOv8 weights (.pt file).
                        Use "yolov8s.pt" for the pretrained COCO model,
                        or a path to your fine-tuned weights.
            confidence_threshold: Minimum confidence to keep a detection.
            iou_threshold: IoU threshold for Non-Maximum Suppression.
            device: Device string ("cpu", "cuda:0", etc.). None = auto.
            imgsz: Input image size for the model.
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.imgsz = imgsz

    def detect(
        self,
        image: str | Path | np.ndarray,
        extract_crops: bool = True,
        source_name: Optional[str] = None,
    ) -> DetectionResult:
        """Run stamp detection on a single image.

        Args:
            image: File path or BGR numpy array.
            extract_crops: If True, crop each detected stamp region.
            source_name: Optional name for the source image in results.

        Returns:
            DetectionResult with all detected stamps.
        """
        # Load image if path is provided
        if isinstance(image, (str, Path)):
            source_name = source_name or Path(image).name
            img_bgr = cv2.imread(str(image))
            if img_bgr is None:
                raise FileNotFoundError(f"Cannot read image: {image}")
        else:
            source_name = source_name or "array_input"
            img_bgr = image

        h, w = img_bgr.shape[:2]

        # Run inference
        results = self.model.predict(
            source=img_bgr,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )

        # Parse results
        result = results[0]
        inference_time_ms = (result.speed["preprocess"]
                             + result.speed["inference"]
                             + result.speed["postprocess"])

        detections: list[StampDetection] = []
        if result.boxes is not None and len(result.boxes) > 0:
            boxes = result.boxes
            for i, (xyxy, conf, cls) in enumerate(
                zip(boxes.xyxy.cpu().numpy(),
                    boxes.conf.cpu().numpy(),
                    boxes.cls.cpu().numpy())
            ):
                x1, y1, x2, y2 = map(int, xyxy)
                class_name = self.model.names[int(cls)]

                # Extract crop if requested
                crop = None
                if extract_crops:
                    # Clamp to image bounds
                    cx1 = max(0, x1)
                    cy1 = max(0, y1)
                    cx2 = min(w, x2)
                    cy2 = min(h, y2)
                    crop = img_bgr[cy1:cy2, cx1:cx2].copy()

                det = StampDetection(
                    stamp_id=f"STAMP_{i+1:03d}",
                    bbox_xyxy=(x1, y1, x2, y2),
                    confidence=float(conf),
                    class_name=class_name,
                    crop=crop,
                )
                detections.append(det)

        # Sort by confidence descending
        detections.sort(key=lambda d: d.confidence, reverse=True)

        return DetectionResult(
            source_image=source_name,
            image_shape=(h, w),
            detections=detections,
            inference_time_ms=inference_time_ms,
        )

    def detect_batch(
        self,
        image_paths: list[str | Path],
        extract_crops: bool = True,
    ) -> list[DetectionResult]:
        """Run stamp detection on multiple images.

        Args:
            image_paths: List of image file paths.
            extract_crops: If True, crop each detected stamp region.

        Returns:
            List of DetectionResult, one per input image.
        """
        return [
            self.detect(p, extract_crops=extract_crops)
            for p in image_paths
        ]

    def save_crops(
        self,
        result: DetectionResult,
        output_dir: str | Path,
        prefix: Optional[str] = None,
    ) -> list[Path]:
        """Save cropped stamp images to disk.

        Args:
            result: DetectionResult from detect().
            output_dir: Directory to save crops.
            prefix: Optional filename prefix (default: source image stem).

        Returns:
            List of paths to saved crop images.
        """
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
        """Draw detection boxes on the image for visualization.

        Args:
            image: Original BGR image.
            result: DetectionResult from detect().
            show_labels: Whether to draw class + confidence labels.
            line_thickness: Thickness of bounding box lines.

        Returns:
            Annotated BGR image.
        """
        annotated = image.copy()
        for det in result.detections:
            x1, y1, x2, y2 = det.bbox_xyxy

            # Color based on confidence: green (high) -> yellow -> red (low)
            if det.confidence >= 0.7:
                color = (0, 200, 0)       # Green
            elif det.confidence >= 0.5:
                color = (0, 200, 255)     # Yellow/Orange
            else:
                color = (0, 0, 255)       # Red

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
