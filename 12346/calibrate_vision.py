"""
Calibration Tool - Prints cell values to find the right threshold
"""
import cv2
import numpy as np
import os
from vision_pipeline import VisionPipeline

def main():
    pipeline = VisionPipeline()
    print("Capturing screen...")
    img = pipeline.capture_screen()
    board_img, _ = pipeline.detect_regions(img)
    board_gray, _ = pipeline.preprocess_image(board_img)
    
    h, w = board_gray.shape
    cell_h = h / 8
    cell_w = w / 8
    
    print("\n--- CELL VALUES (Max Brightness) ---")
    print("   0   1   2   3   4   5   6   7")
    print("  -------------------------------")
    
    for r in range(8):
        row_str = f"{r}|"
        for c in range(8):
            y1 = int(r * cell_h + cell_h * 0.3)
            y2 = int((r + 1) * cell_h - cell_h * 0.3)
            x1 = int(c * cell_w + cell_w * 0.3)
            x2 = int((c + 1) * cell_w - cell_w * 0.3)
            
            cell = board_gray[y1:y2, x1:x2]
            if cell.size > 0:
                val = int(np.max(cell))
                row_str += f" {val:3d}"
            else:
                row_str += " ???"
        print(row_str)
        
    print("\n--- CELL VALUES (Standard Deviation) ---")
    print("   0   1   2   3   4   5   6   7")
    print("  -------------------------------")
    
    for r in range(8):
        row_str = f"{r}|"
        for c in range(8):
            y1 = int(r * cell_h + cell_h * 0.3)
            y2 = int((r + 1) * cell_h - cell_h * 0.3)
            x1 = int(c * cell_w + cell_w * 0.3)
            x2 = int((c + 1) * cell_w - cell_w * 0.3)
            
            cell = board_gray[y1:y2, x1:x2]
            if cell.size > 0:
                val = int(np.std(cell))
                row_str += f" {val:3d}"
            else:
                row_str += " ???"
        print(row_str)

    print("\nSo sánh giá trị của ô CÓ BLOCK và ô TRỐNG để chọn ngưỡng phù hợp.")

if __name__ == "__main__":
    main()
