"""
SMART BOT - Tracks block positions after each placement
After placing a block, remaining blocks shift LEFT
"""
import pyautogui
import cv2
import numpy as np
import time
import json
import os
import screenshot_util

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def detect_board(img, config):
    tl = config["board"]["top_left"]
    br = config["board"]["bottom_right"]
    
    board_img = img[tl[1]:br[1], tl[0]:br[0]]
    gray = cv2.cvtColor(board_img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    grid = np.zeros((8, 8), dtype=int)
    cell_h, cell_w = h / 8, w / 8
    
    for r in range(8):
        for c in range(8):
            y1 = int(r * cell_h + cell_h * 0.3)
            y2 = int((r + 1) * cell_h - cell_h * 0.3)
            x1 = int(c * cell_w + cell_w * 0.3)
            x2 = int((c + 1) * cell_w - cell_w * 0.3)
            
            cell = gray[y1:y2, x1:x2]
            if cell.size > 0:
                grid[r, c] = 1 if np.max(cell) > 80 else 0
    
    return grid

def get_cell_position(config, row, col):
    tl = config["board"]["top_left"]
    br = config["board"]["bottom_right"]
    
    width = br[0] - tl[0]
    height = br[1] - tl[1]
    
    x = tl[0] + int((col + 0.5) * width / 8)
    y = tl[1] + int((row + 0.5) * height / 8)
    
    return (x, y)

def fast_drag(from_pos, to_pos):
    pyautogui.moveTo(from_pos[0], from_pos[1])
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(0.1)
    
    steps = 15
    for i in range(1, steps + 1):
        t = i / steps
        x = int(from_pos[0] + (to_pos[0] - from_pos[0]) * t)
        y = int(from_pos[1] + (to_pos[1] - from_pos[1]) * t)
        pyautogui.moveTo(x, y)
        time.sleep(0.01)
    
    pyautogui.moveTo(to_pos[0], to_pos[1])
    time.sleep(0.2)
    pyautogui.mouseUp()
    time.sleep(0.3)

def main():
    print("="*60)
    print("🧠 SMART BOT - Tracks block positions")
    print("="*60)
    
    config = load_config()
    offset_y = config.get("block_offset_y", 463)
    
    # Original 3 block positions (when all 3 blocks are present)
    original_positions = [tuple(p) for p in config.get("block_positions_manual", [])]
    
    print(f"Offset: {offset_y}px")
    print(f"Original positions: {original_positions}")
    
    # Current blocks available (list of positions)
    # After placing block 0, block 1 moves to pos 0, block 2 moves to pos 1
    current_blocks = list(original_positions)  # Copy
    
    move_count = 0
    blocks_placed_in_round = 0
    
    while move_count < 50:
        try:
            # Capture
            screenshot_util.capture_fullscreen("temp/current.png")
            img = cv2.imread("temp/current.png")
            board = detect_board(img, config)
            filled = np.sum(board)
            
            # How many blocks left in this round?
            blocks_left = 3 - blocks_placed_in_round
            
            print(f"\n[Move {move_count+1}] Board: {filled}/64 | Blocks left: {blocks_left}")
            
            # Print board state
            print("  Board State:")
            for r in range(8):
                row_str = "  "
                for c in range(8):
                    row_str += "█" if board[r, c] == 1 else "·"
                print(row_str)
            
            if blocks_left == 0:
                print("  ⏳ All blocks used. Waiting for new blocks...")
                time.sleep(1.5)
                # Reset - new 3 blocks appear
                current_blocks = list(original_positions)
                blocks_placed_in_round = 0
                continue
            
            # Get empty cells
            empty = [(r, c) for r in range(8) for c in range(8) if board[r, c] == 0]
            
            if not empty:
                print("  Board full!")
                break
            
            # Sort empty positions by "openness" (number of empty neighbors)
            # This helps fit larger blocks
            def count_empty_neighbors(pos):
                r, c = pos
                count = 0
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if 0 <= r+dr < 8 and 0 <= c+dc < 8 and board[r+dr, c+dc] == 0:
                            count += 1
                return count
            
            empty.sort(key=count_empty_neighbors, reverse=True)
            
            # Current block position
            if not current_blocks:
                 current_blocks = list(original_positions)
                 blocks_placed_in_round = 0
                 continue

            block_pos = current_blocks[0]
            
            # Find a valid target position (one that keeps cursor on screen)
            screen_width, screen_height = pyautogui.size()
            valid_target_found = False
            
            # Try top 10 best empty positions
            for i in range(min(10, len(empty))):
                # Cycle through best positions based on move count to avoid getting stuck
                idx = (move_count + i) % len(empty)
                target_r, target_c = empty[idx]
                
                raw_pos = get_cell_position(config, target_r, target_c)
                cursor_y = raw_pos[1] + offset_y
                
                # Check if cursor would be off-screen
                if cursor_y >= screen_height - 10:
                    continue
                    
                target_pos = (raw_pos[0], cursor_y)
                valid_target_found = True
                print(f"  Block at {block_pos} -> ({target_r},{target_c}) [Cursor Y: {cursor_y}]")
                break
            
            if not valid_target_found:
                print("  ⚠️ Cannot place block: All targets require cursor off-screen!")
                print("  👉 Please SCROLL UP or MOVE GAME WINDOW HIGHER!")
                time.sleep(1)
                move_count += 1
                continue
            
            # Drag
            fast_drag(block_pos, target_pos)
            
            # Check result
            time.sleep(0.3)
            screenshot_util.capture_fullscreen("temp/after.png")
            img_after = cv2.imread("temp/after.png")
            board_after = detect_board(img_after, config)
            filled_after = np.sum(board_after)
            
            if filled_after != filled:
                print(f"  ✅ Success! {filled} -> {filled_after}")
                
                # Block was placed! Remove it and shift remaining blocks LEFT
                current_blocks.pop(0)  # Remove first block
                blocks_placed_in_round += 1
                
                print(f"  Remaining blocks: {current_blocks}")
            else:
                print(f"  ❌ No change (position might not fit)")
            
            move_count += 1
            
        except KeyboardInterrupt:
            print("\n🛑 Stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(0.5)
    
    print("\n🏁 DONE")

if __name__ == "__main__":
    if not os.path.exists("temp"):
        os.makedirs("temp")
    print("⚠️ Starting in 2 seconds...")
    time.sleep(2)
    main()
