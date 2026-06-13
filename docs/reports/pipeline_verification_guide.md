# 🔍 Pipeline Verification Guide

This guide outlines the specific steps for the team to locally verify the end-to-end functionality of our passport preprocessing and stamp detection pipeline. 

## Step 1: Verify Preprocessing on the Full Dataset
To quickly verify that the automatic orientation correction, deskewing, and contrast enhancement logic works across all passport samples, run the pipeline smoke test.

1. In your terminal, run the pipeline test script (we skip denoising here for speed):
   ```bash
   python scripts/test_pipeline.py --max-images -1 --skip-denoise
   ```
2. Open the generated `data/processed/test_report.json` to review the processing metrics for every image. You should see details like `rotation_deg`, `deskew_deg`, and `processing_time_s`.
3. Visually review the enhanced images in the `data/processed/enhanced/` folder to ensure all rotated pages were correctly detected and righted.
4. **(Optional)** Run the visual comparison script to generate side-by-side grids of the raw vs. enhanced images:
   ```bash
   python scripts/verify_preprocessing.py
   ```
   Check the `data/processed/comparisons/` folder to view the generated grids.

## Step 2: Validate the Stamp Detection Wrapper
The YOLOv8 wrapper (`stamp_detector.py`) is verified to run end-to-end. However, since the baseline COCO model has **no "stamp" class**, the next step is fine-tuning it with actual stamp data.

1. **Annotate:** Use **Roboflow** or **CVAT** to annotate bounding boxes for the stamps in your `data/raw/` images. Export the dataset in YOLOv8 format.
2. **Train Prototype:** Train a small YOLOv8 prototype on the dataset using the Ultralytics CLI:
   ```bash
   yolo detect train data=stamps.yaml model=yolov8s.pt epochs=50 imgsz=640
   ```
3. **Update Wrapper:** Once training is complete, update the `stamp_detector.py` initialization path to point to your new fine-tuned weights:
   ```python
   # In test_pipeline.py or your inference script
   detector = StampDetector(model_path="runs/detect/train/weights/best.pt")
   ```
4. **Re-run Pipeline:** Re-run `test_pipeline.py`. The wrapper will automatically detect stamps and output the cropped stamp images into the `data/processed/annotated/` folder.
5. **Verify Precision/Recall:** Review the cropped images in `data/processed/annotated/` to instantly verify the model's detection accuracy!
