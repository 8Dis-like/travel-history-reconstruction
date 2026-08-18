"""
Resume YOLOv8s-seg fine-tuning with a smaller batch size (batch=4) to prevent OOM,
validate, and then restore original bbox labels.
"""
import os

def main():
    base = r"G:\Abroad\UCLA\MSEng\Capstone\Securiport"
    dataset_dir = os.path.join(base, "data", "synthetic_dataset")
    seg_yaml_path = os.path.join(base, "dataset_seg.yaml")
    
    print("\nStep 2: Fine-tuning YOLOv8s-seg (with batch=4)...")
    from ultralytics import YOLO
    model = YOLO("yolov8s-seg.pt")  # Download pretrained seg model
    model.train(
        data=seg_yaml_path,
        epochs=10,
        imgsz=640,
        batch=4,  # REDUCED BATCH SIZE TO PREVENT OOM
        project="runs/detect",
        name="stamp_finetune_seg_batch4",
        pretrained=True,
    )
    
    print("\nStep 3: Validating YOLOv8s-seg...")
    best_path = os.path.join(base, "runs", "detect", "stamp_finetune_seg_batch4", "weights", "best.pt")
    model = YOLO(best_path)
    results = model.val(data=seg_yaml_path, split="val")
    
    print("\n" + "="*60)
    print("TABLE 4.2: Synthetic Validation (YOLOv8-seg)")
    print("="*60)
    print(f"Box mAP50:      {results.box.map50:.4f}")
    print(f"Box mAP50:95:   {results.box.map:.4f}")
    print(f"Box Precision:  {results.box.mp:.4f}")
    print(f"Box Recall:     {results.box.mr:.4f}")
    print(f"Mask mAP50:     {results.seg.map50:.4f}")
    print(f"Mask mAP50:95:  {results.seg.map:.4f}")
    print(f"Mask Precision: {results.seg.mp:.4f}")
    print(f"Mask Recall:    {results.seg.mr:.4f}")
    print("="*60)
    
    # Restore original bbox labels
    print("\nStep 4: Restoring original bbox labels...")
    for split in ["train", "val"]:
        split_dir = os.path.join(dataset_dir, split)
        labels_orig = os.path.join(split_dir, "labels")
        labels_bbox = os.path.join(split_dir, "labels_bbox")
        labels_seg_restore = os.path.join(split_dir, "labels_seg")
        
        # We rename the active seg labels back to labels_seg
        if os.path.exists(labels_orig):
            # Sometimes Windows locks files, so we handle it gracefully
            try:
                os.rename(labels_orig, labels_seg_restore)
            except FileExistsError:
                # If labels_seg already exists (from convert_split), we can just delete the active one
                import shutil
                shutil.rmtree(labels_orig)
        
        # We rename labels_bbox back to labels (original state)
        if os.path.exists(labels_bbox):
            os.rename(labels_bbox, labels_orig)
            print(f"  Restored {labels_bbox} -> {labels_orig}")

if __name__ == "__main__":
    main()
