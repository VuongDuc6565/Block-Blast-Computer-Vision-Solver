import cv2
import numpy as np

# Load the calibration result or full screenshot
img_path = "temp/calibration_full.png"
if not os.path.exists(img_path):
    print("Error: temp/calibration_full.png not found. Run auto_calibrate.py first.")
    exit()

img = cv2.imread(img_path)

# Board Coordinates found: [210:695, 32:517]
board_y1, board_y2 = 210, 695
board_x1, board_x2 = 32, 517

# Draw Board
cv2.rectangle(img, (board_x1, board_y1), (board_x2, board_y2), (0, 255, 0), 2)
cv2.putText(img, "BOARD", (board_x1, board_y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Estimate Block Positions based on Board Position
# Assuming standard layout relative to board width/height
board_h = board_y2 - board_y1
board_w = board_x2 - board_x1

# Gap between board and blocks
gap = int(board_h * 0.08) 
block_area_h = int(board_h * 0.3)
block_y1 = board_y2 + gap
block_y2 = block_y1 + block_area_h

# 3 Blocks width
block_w = int(board_w / 3)

# Block 1
b1_x1 = board_x1
b1_x2 = b1_x1 + block_w
cv2.rectangle(img, (b1_x1, block_y1), (b1_x2, block_y2), (0, 0, 255), 2)
cv2.putText(img, "BLK 1", (b1_x1, block_y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

# Block 2
b2_x1 = b1_x2
b2_x2 = b2_x1 + block_w
cv2.rectangle(img, (b2_x1, block_y1), (b2_x2, block_y2), (255, 0, 0), 2)
cv2.putText(img, "BLK 2", (b2_x1, block_y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

# Block 3
b3_x1 = b2_x2
b3_x2 = board_x2
cv2.rectangle(img, (b3_x1, block_y1), (b3_x2, block_y2), (0, 255, 255), 2)
cv2.putText(img, "BLK 3", (b3_x1, block_y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

print(f"Estimated Block Coordinates:")
print(f"Block 1: [{block_y1}:{block_y2}, {b1_x1}:{b1_x2}]")
print(f"Block 2: [{block_y1}:{block_y2}, {b2_x1}:{b2_x2}]")
print(f"Block 3: [{block_y1}:{block_y2}, {b3_x1}:{b3_x2}]")

cv2.imwrite("temp/visualize_blocks.png", img)
print("Saved visualization to temp/visualize_blocks.png")
