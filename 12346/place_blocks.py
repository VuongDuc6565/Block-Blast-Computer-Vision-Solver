"""
Place Blocks Logic
Implements Step 6: Place Blocks
"""
import numpy as np
import pyautogui
import time
from vision_pipeline import VisionPipeline

class BlockPlacer:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.config = pipeline.config
        self.offset_y = self.config.get("block_offset_y", 463)
        
    def check_fit(self, board, block_matrix, row, col):
        """Check if block fits at position (row, col)"""
        block_h, block_w = block_matrix.shape
        board_h, board_w = board.shape
        
        # Check boundaries
        if row + block_h > board_h or col + block_w > board_w:
            return False
            
        # Check collision
        for r in range(block_h):
            for c in range(block_w):
                if block_matrix[r, c] == 1:
                    if board[row + r, col + c] == 1:
                        return False
        return True

    def find_best_position(self, board, block_matrix):
        """Find best position for block (heuristic: maximize empty neighbors or just first fit)"""
        valid_positions = []
        
        for r in range(8):
            for c in range(8):
                if self.check_fit(board, block_matrix, r, c):
                    valid_positions.append((r, c))
        
        if not valid_positions:
            return None
            
        # For now, return the first valid position (top-left priority)
        # Or sort by some heuristic (e.g. keep center open)
        return valid_positions[0]

    def place_block(self, block_screen_pos, target_row, target_col):
        """Execute drag and drop"""
        target_pos = self.pipeline.get_cell_center(target_row, target_col)
        # Apply offset
        target_y_with_offset = target_pos[1] + self.offset_y
        
        # Safety check
        screen_w, screen_h = pyautogui.size()
        if target_y_with_offset >= screen_h:
            print(f"⚠️ Target Y ({target_y_with_offset}) is off-screen! Skipping.")
            return False
            
        print(f"Dragging block from {block_screen_pos} to ({target_row}, {target_col}) -> Screen: ({target_pos[0]}, {target_y_with_offset})")
        
        # Drag logic
        pyautogui.moveTo(block_screen_pos[0], block_screen_pos[1])
        time.sleep(0.1)
        pyautogui.mouseDown()
        time.sleep(0.1)
        
        # Smooth move
        steps = 15
        for i in range(1, steps + 1):
            t = i / steps
            x = int(block_screen_pos[0] + (target_pos[0] - block_screen_pos[0]) * t)
            y = int(block_screen_pos[1] + (target_y_with_offset - block_screen_pos[1]) * t)
            pyautogui.moveTo(x, y)
            time.sleep(0.01)
            
        pyautogui.moveTo(target_pos[0], target_y_with_offset)
        time.sleep(0.2)
        pyautogui.mouseUp()
        time.sleep(0.3)
        return True

def main():
    print("="*60)
    print("🧩 PLACEMENT LOGIC TEST")
    print("="*60)
    
    pipeline = VisionPipeline()
    placer = BlockPlacer(pipeline)
    
    # 1. Capture & Analyze Board
    print("1. Analyzing Board...")
    img = pipeline.capture_screen()
    board_img, _ = pipeline.detect_regions(img)
    board_gray, _ = pipeline.preprocess_image(board_img)
    board_grid = pipeline.analyze_board(board_gray)
    
    print("Board State:")
    for r in range(8):
        print("  " + "".join(["█ " if x else ". " for x in board_grid[r]]))
        
    # 2. Simulate a Block (1x1 for testing)
    # In real version, we need Step 5: Analyze Blocks
    print("\n2. Testing with 1x1 Block...")
    block_1x1 = np.array([[1]])
    
    pos = placer.find_best_position(board_grid, block_1x1)
    if pos:
        print(f"✅ Found fit at: {pos}")
        
        # Use first manual block position for test
        block_start = tuple(pipeline.config["block_positions_manual"][0])
        placer.place_block(block_start, pos[0], pos[1])
    else:
        print("❌ No fit found!")

if __name__ == "__main__":
    main()
