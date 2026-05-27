"""Check image dimensions"""
import cv2
import os

temp_dir = "temp"
for f in ["screen.png", "test_screen.png", "fullscreen.png"]:
    path = os.path.join(temp_dir, f)
    if os.path.exists(path):
        img = cv2.imread(path)
        if img is not None:
            print(f"{f}: {img.shape}")
        else:
            print(f"{f}: Failed to read")
