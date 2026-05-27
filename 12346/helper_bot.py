
import tkinter as tk
from tkinter import ttk, Canvas
import threading
import time
import numpy as np
import cv2
from mss import mss
import importlib
import os
import sys

# Ensure temp directory exists
if not os.path.exists("temp"):
    os.makedirs("temp")

# Import the existing solver logic
import calculatePositions

class BlockBlastHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("Trợ Lí Block Blast Tự Động")
        self.root.geometry("400x600")
        self.root.attributes('-topmost', True)  # Keep on top

        self.status_var = tk.StringVar(value="Đang khởi tạo...")
        
        # --- GUI Layout ---
        
        # Status Bar
        self.status_label = ttk.Label(root, textvariable=self.status_var, font=("Arial", 10))
        self.status_label.pack(pady=5)
        
        # Canvas for Board Visualization
        self.canvas_size = 320
        self.cell_size = self.canvas_size // 8
        self.canvas = Canvas(root, width=self.canvas_size, height=self.canvas_size, bg="#222")
        self.canvas.pack(pady=10)
        
        # Solution List
        self.solution_text = tk.Text(root, height=10, width=40, font=("Consolas", 9))
        self.solution_text.pack(pady=5, padx=10)
        
        # Control Buttons (Manual Trigger just in case)
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=5)
        self.btn_solve = ttk.Button(btn_frame, text="Giải Ngay (Thủ công)", command=self.trigger_solve)
        self.btn_solve.pack(side=tk.LEFT, padx=5)
        
        # --- State ---
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.last_piece_signature = None
        self.last_solve_time = 0
        
        # Coordinates for Pieces (from calculatePositions.py)
        # [y1, y2, x1, x2] relative to the screenshot
        self.piece_rois = [
            [733, 880, 32, 193],   # Block 1
            [733, 880, 193, 354],  # Block 2
            [733, 880, 354, 517]   # Block 3
        ]
        
    def log(self, msg):
        print(f"[Helper] {msg}")
        self.solution_text.insert(tk.END, f"{msg}\n")
        self.solution_text.see(tk.END)

    def draw_board(self, board_state, solution_moves=None):
        self.canvas.delete("all")
        
        # Draw grid
        for r in range(8):
            for c in range(8):
                x1 = c * self.cell_size
                y1 = r * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                
                # Base color for empty/filled
                if board_state[r, c] == 1:
                    color = "#555" # Filled
                else:
                    color = "#333" # Empty
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#444")
        
        # Draw moves
        if solution_moves:
            colors = ["#FF3333", "#33FF33", "#3333FF"] # Red, Green, Blue
            for idx, move in enumerate(solution_moves):
                # move structure: [shape, row, col, clearedRows]
                if len(move) < 3: continue
                
                shape = move[0]
                start_r = move[1]
                start_c = move[2]
                color = colors[idx % 3]
                
                # Overlay the piece
                rows, cols = shape.shape
                for pr in range(rows):
                    for pc in range(cols):
                        if shape[pr, pc] == 1:
                            r = start_r + pr
                            c = start_c + pc
                            
                            x1 = c * self.cell_size
                            y1 = r * self.cell_size
                            x2 = x1 + self.cell_size
                            y2 = y1 + self.cell_size
                            
                            # Draw piece block
                            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, stippley='gray50', outline=color, width=2)
                            
                            # Draw number (on proper center block)
                            if pr == rows//2 and pc == cols//2:
                                self.canvas.create_text(x1 + self.cell_size/2, y1 + self.cell_size/2, text=str(idx+1), fill="white", font=("Arial", 14, "bold"))


    def get_piece_presence(self, screen_img):
        """
        Check if pieces are present in the 3 ROIs.
        Returns a list of booleans [True, True, True] if all 3 are occupied.
        """
        occupied = []
        # Convert to gray for simple thresholding
        gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
        
        for roi in self.piece_rois:
            y1, y2, x1, x2 = roi
            # Check bounds
            if y1 >= gray.shape[0] or x1 >= gray.shape[1]: 
                occupied.append(False)
                continue
                
            crop = gray[y1:y2, x1:x2]
            # Simple heuristic: If there's significant brightness/variance, it's a piece.
            # calculatePositions checks for > 170.
            # Let's count pixels > 150
            count = np.count_nonzero(crop > 150)
            occupied.append(count > 50) # Assuming a piece has at least 50 bright pixels
            
        return occupied

    def monitor_loop(self):
        self.status_var.set("Đang theo dõi - Chờ 3 khối mới...")
        
        sct = mss()
        monitor = sct.monitors[1]
        
        stable_counter = 0
        img_buffer = None
        
        while self.is_running:
            try:
                # 1. Capture
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                # 2. Check Presence
                presence = self.get_piece_presence(img)
                
                # We trigger when ALL 3 are present (Start of turn)
                if all(presence):
                    # Check stability (to avoid capturing mid-animation)
                    if img_buffer is not None:
                        # Compare ROIs only
                        diff = 0
                        for roi in self.piece_rois:
                            y1, y2, x1, x2 = roi
                            d = cv2.absdiff(img[y1:y2, x1:x2], img_buffer[y1:y2, x1:x2])
                            diff += np.sum(d)
                            
                        if diff < 5000: # Relatively stable
                            stable_counter += 1
                        else:
                            stable_counter = 0
                    
                    img_buffer = img.copy()
                    
                    if stable_counter > 5: # ~0.5s stable (assuming 10hz loop)
                        # Stable 3 pieces found. Compute Signature.
                        # Simple signature: Mean brightness of the 3 ROIs
                        means = []
                        for roi in self.piece_rois:
                            y1, y2, x1, x2 = roi
                            means.append(np.mean(img[y1:y2, x1:x2]))
                        signature = tuple(means) # (float, float, float)
                        
                        # Check if different from last solved/seen set
                        is_new_set = False
                        if self.last_piece_signature is None:
                            is_new_set = True
                        else:
                            # Distance check
                            dist = sum([abs(a-b) for a,b in zip(signature, self.last_piece_signature)])
                            if dist > 5.0: # Significant change
                                is_new_set = True
                                
                        if is_new_set:
                            self.root.after(0, self.status_var.set, "Phát hiện bộ mới! Đang giải...")
                            self.trigger_solve() 
                            
                            self.last_piece_signature = signature
                            stable_counter = 0 # Reset
                    
                else:
                    # Less than 3 pieces - User is playing or empty
                    stable_counter = 0
                    self.root.after(0, self.status_var.set, f"Đang chờ... ({sum(presence)}/3 khối)")

                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in monitor: {e}")
                time.sleep(1)

    def trigger_solve(self):
        """
        Calls calculatePositions logic.
        """
        self.log("\nĐang tính toán...")
        try:
            # 1. Calculate (Detection)
            # calculatePositions.calculate(0) saves temp/screen.png and uses it.
            # It returns: allSolutions, blocks, coordsUsed, originalBoard
            
            solutions, blocks, coords, board = calculatePositions.calculate(0)
            
            self.log(f"Đã phát hiện {len(blocks)} khối.")
            if len(blocks) != 3:
                self.log("Cảnh báo: Không đủ 3 khối? (Có thể cần điều chỉnh vùng nhận diện)")
            
            # 2. Best Option (Search)
            best_sequence = calculatePositions.bestOption(solutions, 3, board)
            
            if not best_sequence:
                self.log("Không tìm thấy giải pháp!")
                return
            
            # 3. Display
            # best_sequence is typically [Move1, Move2, Move3, FinalBoard]
            # Filter out the final board which is just a 2D array
            moves = [x for x in best_sequence if isinstance(x, list) or (isinstance(x, np.ndarray) and x.shape != (8,8))]
            
            display_moves = best_sequence[:-1] # Remove the final board state
            
            self.log(f"Tìm thấy giải pháp {len(display_moves)} bước.")
            
            # Update Canvas (must be on main thread)
            self.root.after(0, lambda: self.draw_board(board, display_moves))
            
            # Text Log
            log_str = "Gợi ý bước đi:\n"
            for i, move in enumerate(display_moves):
                # move: [shape, row, col, cleared]
                log_str += f"{i+1}. Hàng {move[1]}, Cột {move[2]}\n"
            self.log(log_str)
            
        except Exception as e:
            self.log(f"Lỗi: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    root = tk.Tk()
    app = BlockBlastHelper(root)
    root.mainloop()
