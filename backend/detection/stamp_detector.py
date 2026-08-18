from typing import Optional
from ultralytics import YOLO
from pathlib import Path
import numpy as np
import cv2
from dataclasses import dataclass


@dataclass
class StampDetResult:
    stamp_img: np.ndarray
    bounding_box: list[int]
    confidence: float


@dataclass
class StampSegResult(StampDetResult):
    mask: list[list[int]]


@dataclass
class PageProcessingResult:
    processed_img: np.ndarray
    image_width: float
    image_height: float
    total_stamps_detected: int
    page_stamps: list[StampDetResult]


class StampDetector:
    def __init__(
        self, 
        task: str = "segment",
        imgsz: int = 1280, 
        conf: float = 0.65, 
        iou: float = 0.7, 
        device: str = "cpu",
    ):
        if task == "segment":
            seg_path = Path(__file__).parent / "yolo26s_seg_best.pt"
            self.model = YOLO(model=seg_path)
        else:
            det_path = Path(__file__).parent / "yolo8s_det_best.pt"
            self.model = YOLO(model=det_path)

        self.task = task
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self.device = device

    def detect(self, images: list[np.ndarray]) -> PageProcessingResult:
        results = self.model.predict(
            source=images, 
            conf=self.conf,
            iou=self.iou,
            imgsz=self.imgsz,
            device=self.device,
        )

        pages = []

        for orig_img, result in zip(images, results):
            img_h, img_w = orig_img.shape[:2]
            stamps = []
            processed_image = orig_img.copy()
            num_stamp_detections = 0
            outline_thickness = max(1, int(min(img_h, img_w) * 0.0035))

            if result.boxes is not None:
                num_stamp_detections = len(result.boxes)
                if self.task == "segment" and result.masks is not None:
                    processed_image = orig_img.copy() # cv2.cvtColor(orig_img.copy(), cv2.COLOR_BGR2RGB)
                    for box, conf, mask_points in zip(result.boxes.xyxy, result.boxes.conf, result.masks.xy):
                        points = mask_points.astype(np.int32)
                        hull = cv2.convexHull(points)
                        cv2.polylines(processed_image, [hull], isClosed=True, color=(0, 100, 0), thickness=outline_thickness)

                        hull_mask = np.zeros((img_h, img_w), dtype=np.uint8)
                        cv2.fillConvexPoly(hull_mask, hull, 1)

                        r, g, b = cv2.split(orig_img)
                        alpha = hull_mask * 255
                        rgba_image = cv2.merge([r, g, b, alpha])

                        x, y, w, h = cv2.boundingRect(hull)
                        crop = rgba_image[y:y+h, x:x+w].copy()

                        stamp_info = StampSegResult(
                            stamp_img=crop,
                            bounding_box=box.cpu().numpy().astype(np.int32).tolist(),
                            confidence=float(conf),
                            mask=hull.reshape(-1, 2).tolist()
                        )

                        stamps.append(stamp_info)
                else:
                    processed_image = result.plot(conf=False, labels=False)
                    for box, conf in zip(result.boxes.xyxy, result.boxes.conf):
                        x1, y1, x2, y2 = box.cpu().numpy().astype(np.int32).tolist()
                        crop = orig_img[y1:y2, x1:x2].copy()

                        stamp_info = StampDetResult(
                            stamp_img=crop,
                            bounding_box=[x1, y1, x2, y2],
                            confidence=float(conf)
                        )

                        stamps.append(stamp_info)
            pages.append(
                PageProcessingResult(
                    processed_img=processed_image,
                    image_width=img_w,
                    image_height=img_h,
                    total_stamps_detected=num_stamp_detections,
                    page_stamps=stamps
                )
            )

        return pages
