"""
Debug Vision - Verifies the pipeline steps
"""
import cv2
import numpy as np
import os
from vision_pipeline import VisionPipeline

def print_grid(grid):
    print("\nBoard Matrix:")
    print("   0 1 2 3 4 5 6 7")
    print("  ----------------")
    for r in range(8):
        row_str = f"{r}| "
        for c in range(8):
            row_str += "█ " if grid[r, c] == 1 else ". "
        print(row_str)

def main():
    if not os.path.exists("temp"):
        os.makedirs("temp")
        
    print("="*60)
    print("👁️ VISION PIPELINE DEBUG")
    print("="*60)
    
    pipeline = VisionPipeline()
    
    print("\n1. Capturing Screen...")
    img = pipeline.capture_screen()
    
    print("2. Detecting Regions...")
    board_img, blocks_img = pipeline.detect_regions(img)
    cv2.imwrite("temp/step2_board.png", board_img)
    cv2.imwrite("temp/step2_blocks.png", blocks_img)
    print("   - Saved temp/step2_board.png")
    print("   - Saved temp/step2_blocks.png")
    
    print("3. Preprocessing...")
    board_gray, board_thresh = pipeline.preprocess_image(board_img)
    cv2.imwrite("temp/step3_board_gray.png", board_gray)
    cv2.imwrite("temp/step3_board_thresh.png", board_thresh)
    print("   - Saved temp/step3_board_gray.png")
    
    print("4. Analyzing Board...")
    grid = pipeline.analyze_board(board_gray)
    print_grid(grid)
    print("\n   - Saved temp/debug_board_analysis.png (Check this!)")
    
    print("\n" + "="*60)
    print("✅ DONE. Please review the 'temp' folder images.")

if __name__ == "__main__":
    main()
