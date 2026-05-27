import cv2
import numpy as np
import pyautogui
from mss import mss
from PIL import Image
import os
import time

def auto_calibrate():
    print("Starting Auto-Calibration...")
    print("Please ensure the Block Blast game is visible on your screen.")
    print("Taking screenshot in 3 seconds...")
    time.sleep(3)

    # 1. Take Screenshot
    with mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        # Convert to numpy array (BGRA)
        img = np.array(sct_img)
        # Convert to BGR for OpenCV
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # Save original for debug
    if not os.path.exists("temp"):
        os.makedirs("temp")
    cv2.imwrite("temp/calibration_full.png", img)

    # 2. Preprocess
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Blur to reduce noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Edge detection
    edges = cv2.Canny(blur, 50, 150)
    
    # 3. Find Contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 4. Filter for the Board
    # The board is likely a large square-ish shape
    possible_boards = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 50000: # Filter out small elements
            continue
            
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        
        # Check if it has 4 corners (rectangle)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w)/h
            # The board is roughly square (0.8 to 1.2 aspect ratio)
            if 0.8 < aspect_ratio < 1.2:
                possible_boards.append((area, x, y, w, h, approx))

    # Sort by area, largest first
    possible_boards.sort(key=lambda x: x[0], reverse=True)

    if possible_boards:
        # Best match
        area, x, y, w, h, approx = possible_boards[0]
        
        print(f"\nFOUND BOARD CANDIDATE:")
        print(f"X: {x}, Y: {y}, Width: {w}, Height: {h}")
        print(f"Crop Coordinates: [{y}:{y+h}, {x}:{x+w}]")
        
        # Draw rectangle on image for user verification
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
        cv2.putText(img, "Detected Board", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        cv2.imwrite("temp/calibration_result.png", img)
        print(f"\nSaved result to 'temp/calibration_result.png'. Please check this image!")
        print(f"If the green box matches the game board, update your code with:")
        print(f"imgBoard = img[{y}:{y+h}, {x}:{x+w}]")
        
        return y, y+h, x, x+w
    else:
        print("\nCould not detect the board automatically.")
        print("Please ensure the game is fully visible and not obstructed.")
        print("Check 'temp/calibration_full.png' to see what was captured.")
        return None

if __name__ == "__main__":
    try:
        auto_calibrate()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
