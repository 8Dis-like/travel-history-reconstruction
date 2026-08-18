from ultralytics import YOLO
import os

os.chdir(r"G:\Abroad\UCLA\MSEng\Capstone\Securiport")

print("Loading YOLOv8 model...")
model = YOLO("runs/best_stamp_model.pt")

print("Running validation on synthetic dataset...")
results = model.val(data="dataset.yaml", split="val")

print("\n" + "="*60)
print("TABLE 4.2: Synthetic Validation Dataset Performance (YOLOv8)")
print("="*60)
print(f"Box mAP50:      {results.box.map50:.4f}")
print(f"Box mAP50:95:   {results.box.map:.4f}")
print(f"Box Precision:  {results.box.mp:.4f}")
print(f"Box Recall:     {results.box.mr:.4f}")
print("="*60)
