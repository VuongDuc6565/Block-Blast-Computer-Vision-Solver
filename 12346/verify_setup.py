import sys
import os
import traceback

print("Verifying setup...")

try:
    import cv2
    print("OpenCV imported successfully.")
except ImportError:
    print("Error: OpenCV not found.")

try:
    import mss
    print("mss imported successfully.")
except ImportError:
    print("Error: mss not found.")

try:
    import calculatePositions
    print("calculatePositions imported successfully.")
    
    if hasattr(calculatePositions, 'calculate'):
        print("Function 'calculate' found.")
    else:
        print("Error: Function 'calculate' NOT found in calculatePositions.")
        
    if hasattr(calculatePositions, 'take_screenshot'):
        print("Function 'take_screenshot' found.")
        # Try taking a screenshot
        try:
            img, path = calculatePositions.take_screenshot()
            if img is not None:
                print(f"Screenshot taken successfully. Shape: {img.shape}")
            else:
                print("Error: Screenshot returned None.")
        except Exception as e:
            print(f"Error taking screenshot: {e}")
    else:
        print("Error: Function 'take_screenshot' NOT found in calculatePositions.")

except Exception as e:
    print(f"Error importing calculatePositions: {e}")
    traceback.print_exc()

print("Verification complete.")
