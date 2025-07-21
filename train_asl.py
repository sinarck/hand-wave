import os
from ultralytics import YOLO

# =============================
# CONFIGURATION SECTION
# =============================
# Change these paths and parameters as needed

dataset_yaml = 'asl.yaml'  # Path to your dataset YAML file
default_model = 'yolov8n.pt'  # Choose from yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt
output_dir = 'runs/detect/train'  # Where to save results
epochs = 50  # Number of training epochs
imgsz = 640  # Image size for training
batch = 16   # Batch size

# =============================
# TRAINING SCRIPT
# =============================

def main():
    # Print configuration
    print(f"Training YOLOv8 model for ASL detection")
    print(f"Dataset YAML: {dataset_yaml}")
    print(f"Model: {default_model}")
    print(f"Epochs: {epochs}, Image Size: {imgsz}, Batch: {batch}")
    print(f"Output Directory: {output_dir}")

    # Load model
    model = YOLO(default_model)

    # Train
    model.train(
        data=dataset_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=output_dir,
        name=None,  # Let YOLO auto-name the run
        exist_ok=True  # Overwrite if exists
    )

    print("\nTraining complete! Check the output directory for results and best.pt weights.")

if __name__ == "__main__":
    main() 