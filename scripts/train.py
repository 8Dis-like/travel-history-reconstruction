from ultralytics import YOLO
import os

def main():
    # Load the base model from the project root
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'yolov8s.pt')
    dataset_yaml = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dataset.yaml')
    
    model = YOLO(model_path)
    
    # Fine-tune the model
    results = model.train(
        data=dataset_yaml,
        epochs=10, # Kept smaller for quick initial run, user can adjust
        imgsz=640,
        batch=16,
        project='runs/detect',
        name='stamp_finetune',
        # device='0' # Uncomment this if CUDA is available and you want to enforce GPU
    )
    
if __name__ == '__main__':
    main()
