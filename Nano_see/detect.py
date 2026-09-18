#!/usr/bin/env python3
"""
Simple traffic sign detection using the trained model.
"""

from ultralytics import YOLO
import cv2
import sys
from pathlib import Path
Base_DIR = Path(__file__).resolve().parent

# ─── Load model ──────────────────────────────────────────────
model = YOLO(Base_DIR/"best.pt")

# ─── 1) Image ────────────────────────────────────────────────
def detect_image(path, conf=0.25):
    results = model(path, conf=conf, save=True)
    for r in results:
        print(f"Detected {len(r.boxes)} sign(s)")
        r.show()
    return results

# ─── 2) Video / Webcam ──────────────────────────────────────
def detect_video(source=0, conf=0.25):
    cap = cv2.VideoCapture(source)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, conf=conf, verbose=False)
        cv2.imshow("Detection", results[0].plot())
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()

# ─── 3) Quick run ──────────────────────────────────────────
if __name__ == "__main__":
    import os
    # Change this to your image/video path or 0 for webcam
    img_path = os.path.join("yolo-detection-outputs", "yolov8n-custom", "val_batch0_labels.jpg")
    detect_image(img_path)

    # Uncomment for webcam:
    # detect_video(0)
