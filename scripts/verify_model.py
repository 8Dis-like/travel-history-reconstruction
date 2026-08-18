from ultralytics import YOLO
import os

def main():
    # Load the specific best model weights
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'runs', 'best_stamp_model.pt')
    dataset_yaml = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dataset.yaml')
    
    print(f"Loading model from: {model_path}")
    model = YOLO(model_path)
    
    print(f"Validating model using dataset configuration: {dataset_yaml}")
    # Run validation
    metrics = model.val(
        data=dataset_yaml,
        split='val',
        save_json=True, # Optional: save validation results to JSON
        project='runs/detect',
        name='stamp_verification'
    )
    
    print("\n" + "="*50)
    print("VERIFICATION RESULTS:")
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    print(f"Precision: {metrics.box.p.mean():.4f} (Wait, exact property varies depending on version. Let's print metrics.box.mean_results())")
    print(metrics.box.mean_results())
    print("="*50 + "\n")

if __name__ == '__main__':
    main()
