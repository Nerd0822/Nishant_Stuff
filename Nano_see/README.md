# YOLO Nano Model - Traffic Sign Detection

A traffic sign detection system using a custom-trained YOLOv8n (nano) model. This project includes both inference scripts and training outputs.

## Features

- **Image Detection** – Detect traffic signs in static images
- **Video/Webcam Detection** – Real-time detection from video files or webcam feed
- **Trained Model** – Custom YOLOv8n model with training results and metrics

## Project Structure

```
Yolo_nano_model/
├── detect.py                           # Inference script (image + video/webcam)
├── traffic sign detection.ipynb        # Training notebook
└── yolo-detection-outputs/
    └── yolov8n-custom/                 # Training outputs
        ├── weights/
        │   ├── best.pt                 # Best trained weights
        │   └── last.pt                 # Last epoch weights
        ├── results.png                 # Training metrics
        ├── confusion_matrix.png        # Confusion matrix
        ├── labels.jpg                  # Label examples
        └── ...
```

## Quick Start

### Prerequisites

- Python 3.10+

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run detection on an image
python detect.py
```

### Usage

```python
from ultralytics import YOLO

model = YOLO("yolo-detection-outputs/yolov8n-custom/weights/best.pt")

# Detect on image
results = model("path/to/image.jpg", conf=0.25, save=True)

# Detect from webcam
# detect_video(0)
```

## Training

The training notebook `traffic sign detection.ipynb` contains the complete pipeline:
1. Dataset preparation
2. Model configuration (YOLOv8n)
3. Training with hyperparameters
4. Evaluation and metrics

## Results

Training outputs in `yolo-detection-outputs/yolov8n-custom/` include:
- Precision-Recall curves
- F1 score curves
- Confusion matrices
- Training/validation batch samples
- Result CSV with per-epoch metrics

## Tech Stack

- **ultralytics** – YOLOv8 framework
- **OpenCV** – Image/video processing
- **PyTorch** – Deep learning backend