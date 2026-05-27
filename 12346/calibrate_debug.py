import os
import sys

log_file = "calibrate_debug.log"

def log(msg):
    with open(log_file, "a") as f:
        f.write(msg + "\n")

log("Starting calibration script...")

try:
    import pyautogui
    log("Imported pyautogui")
    from mss import mss
    log("Imported mss")
    from PIL import Image
    log("Imported PIL")
    
    log("Taking screenshot...")
    with mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        img.save("temp/calibration_screenshot.png")
    log("Screenshot saved")
    
except Exception as e:
    log(f"Error: {e}")

log("Done")
