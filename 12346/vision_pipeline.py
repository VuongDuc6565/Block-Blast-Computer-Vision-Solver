"""
Vision Pipeline Module
Implements the strict pipeline: Capture -> Detect -> Preprocess -> Analyze -> Place
"""
import cv2
import numpy as np
import json
import screenshot_util

class VisionPipeline:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
    def capture_screen(self):
        """Step 1: Capture Screen"""
        return screenshot_util.capture_fullscreen("temp/vision_input.png")

    def detect_regions(self, img):
        """Step 2: Detect Regions (Board and Blocks)"""
        tl = self.config["board"]["top_left"]
        br = self.config["board"]["bottom_right"]
        
        # Board Area
        board_img = img[tl[1]:br[1], tl[0]:br[0]]
        
        # Blocks Area (estimated below board)
        # Using the manual positions to define a bounding box for blocks might be safer
        # or just a fixed area below the board
        board_height = br[1] - tl[1]
        blocks_top = br[1] + 20
        blocks_bottom = min(img.shape[0], br[1] + 300)
        blocks_left = tl[0] - 50 # Wider to catch side blocks
        blocks_right = br[0] + 50
        
        blocks_img = img[blocks_top:blocks_bottom, blocks_left:blocks_right]
        
        return board_img, blocks_img

    def preprocess_image(self, img):
        """Step 3: Preprocess Images (Grayscale, Noise Reduction, Threshold)"""
        if img.size == 0:
            return None
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Adaptive Thresholding for better stability than fixed threshold
        # This helps when lighting/background changes
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Invert so blocks are white, background is black (usually)
        # But in Block Blast, empty cells are dark, filled are colorful/bright.
        # Let's stick to simple thresholding if adaptive is too noisy, 
        # but the user asked for "Normalize... reduce noise".
        
        return gray, thresh

    def analyze_board(self, board_gray):
        """Step 4: Analyze Board State"""
        h, w = board_gray.shape
        grid = np.zeros((8, 8), dtype=int)
        
        cell_h = h / 8
        cell_w = w / 8
        
        # Debug visualization
        debug_img = cv2.cvtColor(board_gray, cv2.COLOR_GRAY2BGR)
        
        for r in range(8):
            for c in range(8):
                # Sample the center of the cell (avoid borders)
                y1 = int(r * cell_h + cell_h * 0.3)
                y2 = int((r + 1) * cell_h - cell_h * 0.3)
                x1 = int(c * cell_w + cell_w * 0.3)
                x2 = int((c + 1) * cell_w - cell_w * 0.3)
                
                cell = board_gray[y1:y2, x1:x2]
                
                if cell.size > 0:
                    # Analyze cell statistics
                    mean_val = np.mean(cell)
                    std_val = np.std(cell)
                    max_val = np.max(cell)
                    
                    # Calibration Data Analysis:
                    # Empty cells: ~43-80 (Max Brightness)
                    # Filled cells: ~144-190 (Max Brightness)
                    # Threshold: 100 seems safe
                    
                    is_filled = 1 if max_val > 100 else 0
                    grid[r, c] = is_filled
                    
                    # Draw on debug image
                    color = (0, 0, 255) if is_filled else (0, 255, 0)
                    cv2.rectangle(debug_img, (x1, y1), (x2, y2), color, 1)
                    cv2.putText(debug_img, f"{int(max_val)}", (x1, y1+10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)

        cv2.imwrite("temp/debug_board_analysis.png", debug_img)
        return grid

    def get_cell_center(self, row, col):
        tl = self.config["board"]["top_left"]
        br = self.config["board"]["bottom_right"]
        width = br[0] - tl[0]
        height = br[1] - tl[1]
        
        x = tl[0] + int((col + 0.5) * width / 8)
        y = tl[1] + int((row + 0.5) * height / 8)
        return (x, y)
