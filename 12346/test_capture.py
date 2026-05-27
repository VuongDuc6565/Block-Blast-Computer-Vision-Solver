import calculatePositions
import traceback
import sys
import os

LOG_FILE = r"E:\ComputerVision\Block-Blast-Data-Analyst\python_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(str(msg) + "\n")

log("Starting test_capture.py...")
try:
    log("Calling calculatePositions.calculate(0)...")
    output, blocks, coordsUsed, board = calculatePositions.calculate(0)
    log("Calculation finished successfully!")
    log(f"Number of solutions found: {len(output)}")
    log(f"Number of blocks detected: {len(blocks)}")
    log("Board state:")
    log(board)
except Exception as e:
    log("An error occurred:")
    log(e)
    with open("debug_log.txt", "a") as f:
        traceback.print_exc(file=f)
