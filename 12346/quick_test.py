"""Quick test of screenshot functionality"""
import sys
import os

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

print("Starting test...", flush=True)

try:
    from mss import mss
    from PIL import Image
    import cv2
    print("1. Imports OK", flush=True)
    
    # Test screenshot
    print("2. Taking screenshot...", flush=True)
    with mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        img.save("temp/test_debug.png")
    print(f"3. Screenshot saved to temp/test_debug.png", flush=True)
    
    # Test reading with OpenCV
    print("4. Reading with OpenCV...", flush=True)
    img_cv = cv2.imread("temp/test_debug.png", 1)
    if img_cv is None:
        print("ERROR: cv2.imread returned None!", flush=True)
    else:
        print(f"5. Image shape: {img_cv.shape}", flush=True)
        
    # Test cropping (same as calculatePositions.py)
    print("6. Testing crop [360:1190, 173:1000]...", flush=True)
    imgBoard = img_cv[360:1190, 173:1000]
    print(f"7. Cropped shape: {imgBoard.shape}", flush=True)
    
    print("\nAll tests passed!", flush=True)
    
except Exception as e:
    import traceback
    print(f"\nERROR: {type(e).__name__}: {e}", flush=True)
    traceback.print_exc()
