import mss
import numpy as np
import cv2
import ctypes

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

def capture_fullscreen(output_path="screenshot.png"):
    with mss.mss() as sct:
        # Get the first monitor
        monitor = sct.monitors[1]
        
        # Capture the screen
        sct_img = sct.grab(monitor)
        
        # Convert to numpy array
        img = np.array(sct_img)
        
        # Convert BGRA to BGR
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Save to file
        cv2.imwrite(output_path, img)
        return img
