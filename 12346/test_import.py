import os
LOG_FILE = r"E:\ComputerVision\Block-Blast-Data-Analyst\import_log.txt"
def log(msg):
    with open(LOG_FILE, "a") as f: f.write(str(msg) + "\n")

log("Start")
try:
    import cv2
    log("cv2 imported")
except Exception as e:
    log(f"cv2 failed: {e}")

try:
    import mss
    log("mss imported")
except Exception as e:
    log(f"mss failed: {e}")

try:
    import numpy
    log("numpy imported")
except Exception as e:
    log(f"numpy failed: {e}")

try:
    import calculatePositions
    log("calculatePositions imported")
except Exception as e:
    log(f"calculatePositions failed: {e}")
