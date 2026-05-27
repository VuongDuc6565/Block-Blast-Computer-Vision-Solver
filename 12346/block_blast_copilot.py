# -*- coding: utf-8 -*-
"""
Block Blast Copilot Mode - Tích hợp vision logic từ code gốc
Chỉ chụp 1 lần đầu để setup, sau đó tự động chụp mỗi 8s và xử lý
"""
import os
import cv2
import numpy as np
import tkinter as tk
import tkinter.font as tkfont
from typing import List, Tuple, Dict, Optional
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import time
from mss import mss
import itertools

# =============================================================================
# SCREEN CAPTURE MODULE
# =============================================================================
class ScreenCapture:
    """Module chụp màn hình game"""
    def __init__(self):
        self.board_region = None
        self.pieces_region = None
        
    def set_board_region(self, x: int, y: int, width: int, height: int):
        self.board_region = {"left": x, "top": y, "width": width, "height": height}
        
    def set_pieces_region(self, x: int, y: int, width: int, height: int):
        self.pieces_region = {"left": x, "top": y, "width": width, "height": height}
        
    def capture_board(self, save_path=None) -> Optional[np.ndarray]:
        if not self.board_region: return None
        return self._capture_region(self.board_region, save_path)
        
    def capture_pieces(self, save_path=None) -> Optional[np.ndarray]:
        if not self.pieces_region: return None
        return self._capture_region(self.pieces_region, save_path)
        
    def _capture_region(self, region, save_path=None):
        try:
            with mss() as sct:
                screenshot = sct.grab(region)
                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                if save_path:
                    cv2.imwrite(save_path, img)
                return img
        except Exception as e:
            print(f"Lỗi chụp màn hình: {e}")
            return None
    
    def capture_full_screen(self) -> Optional[np.ndarray]:
        """Chụp toàn màn hình"""
        try:
            with mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img
        except Exception as e:
            print(f"Lỗi chụp toàn màn hình: {e}")
            return None

# =============================================================================
# VISION MODULE (GIỮ NGUYÊN TỪ CODE GỐC)
# =============================================================================
class BlockBlastVision:
    """Xử lý ảnh để trích xuất board."""
    def __init__(self, grid_size: int = 8):
        self.grid_size = grid_size

    def extract_board_from_image(self, image_path: str) -> np.ndarray:
        """Trích xuất board từ ảnh Block Blast (đã crop hoặc full)."""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Không thể đọc ảnh: {image_path}")
            
            # Nếu ảnh gần vuông (tỷ lệ 0.8-1.2) và > 200px -> giả định là crop sẵn
            h, w = image.shape[:2]
            if 0.8 < w/h < 1.2 and w > 200:
                # Dùng trực tiếp, nhưng vẫn cho qua _find_board_region để sure
                # Nếu find fail thì fallback về toàn bộ ảnh
                pass 
                
            board_region = self._find_board_region(image)
            x, y, w_rect, h_rect = board_region
            board_image = image[y:y+h_rect, x:x+w_rect]
            size = min(board_image.shape[:2])
            board_image = cv2.resize(board_image, (size, size))
            board = self._extract_grid_cells_improved(board_image)
            # self._debug_board(board)
            return board
        except Exception as e:
            print(f"Lỗi khi xử lý ảnh board: {e}")
            return self._create_fallback_board()

    def _find_board_region(self, image):
        """Tìm vùng board trong ảnh Block Blast"""
        h, w = image.shape[:2]
        # Nếu ảnh đã crop (gần vuông), trả về toàn bộ
        if 0.9 < w/max(1,h) < 1.1:
             return (0, 0, w, h)
             
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_contour = None
        best_score = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 10000:
                continue
            x, y, w_rect, h_rect = cv2.boundingRect(contour)
            ar = w_rect / max(1, h_rect)
            if 0.7 <= ar <= 1.3:
                score = area * (1 - abs(1 - ar))
                if score > best_score:
                    best_score = score
                    best_contour = contour
        if best_contour is not None:
            x, y, w_rect, h_rect = cv2.boundingRect(best_contour)
            return (x, y, w_rect, h_rect)
        else:
            # Fallback về center crop
            size = min(w, h)
            x = (w - size) // 2
            y = (h - size) // 2
            return (x, y, size, size)

    def _extract_grid_cells_improved(self, image):
        """Chia ảnh thành grid cells và phân tích màu"""
        h, w = image.shape[:2]
        cell_size = min(h, w) // self.grid_size
        margin = int(cell_size * 0.1)
        board = np.zeros((self.grid_size, self.grid_size), dtype=int)
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                y1 = max(0, row * cell_size + margin)
                y2 = min(h, (row + 1) * cell_size - margin)
                x1 = max(0, col * cell_size + margin)
                x2 = min(w, (col + 1) * cell_size - margin)
                cell = image[y1:y2, x1:x2]
                if cell.size == 0:
                    continue
                color_code = self._analyze_cell_color_improved(cell)
                board[row, col] = color_code
        return board

    def _analyze_cell_color_improved(self, cell):
        """Phân tích màu cell"""
        if cell.size == 0:
            return 0
        hsv = cv2.cvtColor(cell, cv2.COLOR_BGR2HSV)
        h, s, v = np.mean(hsv, axis=(0, 1))
        if v < 100 or s < 40:
            return 0
        if h < 10 or h > 170: return 1
        elif 10 <= h < 25: return 2
        elif 25 <= h < 45: return 3
        elif 45 <= h < 75: return 4
        elif 75 <= h < 105: return 5
        elif 105 <= h < 135: return 6
        elif 135 <= h < 165: return 7
        else: return 8

    def _debug_board(self, board):
        """In debug"""
        print("\n=== DEBUG BOARD ===")
        for r in range(board.shape[0]):
            row_str = "".join("." if board[r, c] == 0 else str(board[r, c]) for c in range(board.shape[1]))
            print(f"Row {r}: {row_str}")
        total = board.size
        empty = np.sum(board == 0)
        print(f"Fill ratio: {(total-empty)/total*100:.1f}%")
        print("==================\n")

    def _create_fallback_board(self):
        """Board fallback"""
        return np.zeros((self.grid_size, self.grid_size), dtype=int)

# =============================================================================
# PIECES EXTRACTOR (Cập nhật với template matching)
# =============================================================================
class PiecesExtractor:
    """Trích xuất 3 pieces từ ảnh (valley projection + template matching)"""
    def __init__(self, vision_for_board: BlockBlastVision = None):
        self.vision = vision_for_board
        
        # Template matching cho các hình dạng đặc biệt (L-shapes)
        # Shape A: dạng '7' (3x3)
        self.shape_A = np.array([[1, 1, 1], [0, 0, 1], [0, 0, 1]], dtype=int)
        # Shape B: dạng '┘' (3x3)
        self.shape_B = np.array([[0, 0, 1], [0, 0, 1], [1, 1, 1]], dtype=int)
        
        self.template_A = self._get_template(self.shape_A)
        self.template_B = self._get_template(self.shape_B)
    
    def _get_template(self, shape):
        """Convert shape array thành image template"""
        size = shape.shape[0]
        template = np.ones((size * 40 + 2, size * 40 + 2, 3), dtype=np.uint8) * 255
        for r, c in np.argwhere(shape == 1):
            y1, x1 = r * 40 + 1, c * 40 + 1
            y2, x2 = (r + 1) * 40 + 1, (c + 1) * 40 + 1
            cv2.rectangle(template, (x1, y1), (x2, y2), (80, 80, 80), -1)
        return template
    
    def extract_pieces_from_crop(self, image_path: str) -> List[np.ndarray]:
        """API MỚI: Xử lý trực tiếp từ ảnh crop vùng pieces"""
        img = cv2.imread(image_path)
        if img is None:
            return [np.array([[1]]*3)] # Dummy fallback
            
        # Tìm boxes trực tiếp trên ảnh crop
        # Giả sử ảnh crop là chiều ngang chứa 3 pieces
        H, W = img.shape[:2]
        
        # Tiền xử lý để tìm contours
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Mask giữ lại các màu sáng (pieces)
        mask = cv2.inRange(hsv, (8, 60, 80), (165, 255, 255))
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        boxes = []
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            area = w * h
            # Filter nhiễu: diện tích quá nhỏ hoặc quá lớn so với toàn ảnh
            if area < (H*W) * 0.01: continue 
            boxes.append((x, y, w, h))
            
        # Sort theo trục x để lấy 3 pieces từ trái sang phải
        boxes = sorted(boxes, key=lambda b: b[0])
        
        # Nếu có quá nhiều box gần nhau, merge lại hoặc lấy top 3 to nhất?
        # Đơn giản lấy top 3 (hoặc ít hơn)
        
        # Xử lý từng box
        pieces = []
        for (x, y, w, h) in boxes:
            pad = 5
            xs, ys = max(0, x - pad), max(0, y - pad)
            xe, ye = min(W, x + w + pad), min(H, y + h + pad)
            roi = img[ys:ye, xs:xe]
            
            # Decode logic cũ
            piece = self._process_roi_to_grid(roi)
            pieces.append(piece)
            
        while len(pieces) < 3:
            pieces.append(np.array([[1]]))
            
        return pieces[:3]
        
    def _process_roi_to_grid(self, roi):
        """Logic decode grid từ ROI (refactored từ extract_pieces cũ)"""
        if roi.size == 0: return np.array([[1]])
        
        # Template checks
        try:
            res_A = cv2.matchTemplate(roi, self.template_A, cv2.TM_CCOEFF_NORMED)
            if np.max(res_A) > 0.8: return self.shape_A.copy()
            res_B = cv2.matchTemplate(roi, self.template_B, cv2.TM_CCOEFF_NORMED)
            if np.max(res_B) > 0.8: return self.shape_B.copy()
        except: pass
        
        # Valley projection fallback
        grid = self._decode_grid_from_roi(roi)
        clean = self._clean_grid_by_component(grid)
        
        # Trim
        if clean.size > 0 and np.sum(clean) > 0:
            rr = np.where(clean.sum(axis=1) > 0)[0]
            cc = np.where(clean.sum(axis=0) > 0)[0]
            if len(rr) > 0 and len(cc) > 0:
                return clean[rr[0]:rr[-1]+1, cc[0]:cc[-1]+1]
        return np.array([[1]])

    # ... (Giữ lại các hàm helper _seams_by_projection, _decode_grid_from_roi, etc.)

    def _seams_by_projection(self, g: np.ndarray, axis: int):
        prof = cv2.GaussianBlur(g, (11, 1), 0).mean(axis=1) if axis == 0 else cv2.GaussianBlur(g, (1, 11), 0).mean(axis=0)
        pmin, pmax = prof.min(), prof.max()
        if pmax - pmin < 1e-3: return []
        norm = (prof - pmin) / (pmax - pmin)
        thr = float(norm.mean() - 0.20)
        idxs = np.where(norm < thr)[0]
        if not idxs.size: return []
        seams, start = [], idxs[0]
        for i in range(1, len(idxs)):
            if idxs[i] != idxs[i-1] + 1:
                seams.append((start + idxs[i-1]) // 2); start = idxs[i]
        seams.append((start + idxs[-1]) // 2)
        merged = []
        min_sep = max(6, int(g.shape[axis] * 0.06))
        for s in seams:
            if not merged or s - merged[-1] >= min_sep:
                merged.append(s)
            else:
                merged[-1] = int((merged[-1] + s) / 2)
        return [s for s in merged if 3 < s < (g.shape[axis] - 3)]

    def _bounds_simple(self, length, seams):
        bounds = sorted(list(set([0] + seams + [length])))
        return [(bounds[i], bounds[i+1]) for i in range(len(bounds)-1)]

    def _decode_grid_from_roi(self, roi_bgr: np.ndarray) -> np.ndarray:
        if roi_bgr.shape[0] < 10 or roi_bgr.shape[1] < 10:
            return np.array([[1]])
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        rows = self._seams_by_projection(gray, axis=0)
        cols = self._seams_by_projection(gray, axis=1)
        rb = self._bounds_simple(gray.shape[0], rows)
        cb = self._bounds_simple(gray.shape[1], cols)
        hsv = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2HSV)
        grid = np.zeros((len(rb), len(cb)), dtype=int)
        for i, (rs, re) in enumerate(rb):
            for j, (cs, ce) in enumerate(cb):
                cell = hsv[rs:re, cs:ce]
                if cell.size == 0: continue
                h, s, v = cv2.split(cell)
                is_piece = ((h > 8) & (h < 165) & (s > 60) & (v > 80)).mean()
                grid[i, j] = 1 if is_piece > 0.40 else 0
        return grid

    def _clean_grid_by_component(self, grid: np.ndarray) -> np.ndarray:
        if grid.size == 0 or np.sum(grid) == 0:
            return grid
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(grid.astype(np.uint8), 4, cv2.CV_32S)
        if num_labels <= 1:
            return grid
        largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        return np.where(labels == largest, 1, 0).astype(int)

    def extract_pieces(self, image_path: str) -> List[np.ndarray]:
        """API chính: trả về đúng 3 piece (grid 0/1) với template matching"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Không thể đọc ảnh: {image_path}")
        board = self._find_board_region(img)
        boxes = self._find_piece_boxes(img, board)
        
        print(f"\n=== PIECES EXTRACTION ===")
        print(f"Found {len(boxes)} piece boxes")
        
        pieces = []
        H, W = img.shape[:2]
        for idx, (x, y, w, h) in enumerate(boxes):
            pad = int(max(w, h) * 0.15)
            xs, ys = max(0, x - pad), max(0, y - pad)
            xe, ye = min(W, x + w + pad), min(H, y + h + pad)
            roi = img[ys:ye, xs:xe]
            
            # Decode grid từ ROI
            grid = self._decode_grid_from_roi(roi)
            clean = self._clean_grid_by_component(grid)
            
            # Template matching cho L-shapes
            try:
                result_A = cv2.matchTemplate(roi, self.template_A, cv2.TM_CCOEFF_NORMED)
                result_B = cv2.matchTemplate(roi, self.template_B, cv2.TM_CCOEFF_NORMED)
                threshold = 0.8
                
                if np.max(result_A) > threshold:
                    clean = self.shape_A.copy()
                    print(f"Piece {idx+1}: Matched Shape A (7-shape)")
                elif np.max(result_B) > threshold:
                    clean = self.shape_B.copy()
                    print(f"Piece {idx+1}: Matched Shape B (┘-shape)")
                else:
                    print(f"Piece {idx+1}: Grid {clean.shape}, filled cells: {np.sum(clean)}")
            except:
                print(f"Piece {idx+1}: Template matching failed, using grid")
            
            # Trim piece
            if clean.size > 0 and np.sum(clean) > 0:
                rr = np.where(clean.sum(axis=1) > 0)[0]
                cc = np.where(clean.sum(axis=0) > 0)[0]
                if len(rr) > 0 and len(cc) > 0:
                    piece = clean[rr[0]:rr[-1]+1, cc[0]:cc[-1]+1]
                else:
                    piece = np.array([[1]])
            else:
                piece = np.array([[1]])
            pieces.append(piece)
        
        while len(pieces) < 3:
            pieces.append(np.array([[1]]))
        
        print(f"Extracted {len(pieces)} pieces")
        print("=========================\n")
        return pieces[:3]

# =============================================================================
# SOLVER MODULE (GIỮ NGUYÊN TỪ CODE GỐC)
# =============================================================================
class BlockBlastSolver:
    """Solver đơn giản"""
    def __init__(self, grid_size: int = 8):
        self.grid_size = grid_size

    def solve_with_heuristics(self, board: np.ndarray, pieces: List[np.ndarray]):
        best_move, best_score = None, -1
        for piece_idx, piece in enumerate(pieces):
            for r in range(self.grid_size - piece.shape[0] + 1):
                for c in range(self.grid_size - piece.shape[1] + 1):
                    if self._can_place(board, piece, r, c):
                        score = self._calculate_score(board, piece, r, c)
                        if score > best_score:
                            best_score = score
                            board_after = self._place_and_clear(board, piece, r, c)
                            best_move = {
                                'piece_index': piece_idx,
                                'position': [r, c],
                                'score': score,
                                'board_after': board_after,
                                'piece_used': piece
                            }
        return best_move

    def _can_place(self, board, piece, row, col):
        for r in range(piece.shape[0]):
            for c in range(piece.shape[1]):
                if piece[r, c] == 1:
                    br, bc = row + r, col + c
                    if br >= self.grid_size or bc >= self.grid_size or board[br, bc] != 0:
                        return False
        return True

    def _calculate_score(self, board, piece, row, col):
        b_temp = board.copy()
        piece_size = 0
        for r in range(piece.shape[0]):
            for c in range(piece.shape[1]):
                if piece[r, c] == 1:
                    b_temp[row + r, col + c] = 1
                    piece_size += 1
        score = piece_size
        cleared_lines = 0
        for r in range(self.grid_size):
            if np.all(b_temp[r, :] != 0):
                cleared_lines += 1
        for c in range(self.grid_size):
            if np.all(b_temp[:, c] != 0):
                cleared_lines += 1
        if cleared_lines > 0:
            score += (10 * cleared_lines) * cleared_lines
        score -= self._count_holes(b_temp)
        return score

    def _clear_lines(self, board: np.ndarray) -> np.ndarray:
        b = board.copy()
        rows_to_clear = [r for r in range(self.grid_size) if np.all(b[r, :] != 0)]
        cols_to_clear = [c for c in range(self.grid_size) if np.all(b[:, c] != 0)]
        if rows_to_clear or cols_to_clear:
            for r in rows_to_clear:
                b[r, :] = 0
            for c in cols_to_clear:
                b[:, c] = 0
        return b

    def _place_and_clear(self, board, piece, row, col):
        b = board.copy()
        for r in range(piece.shape[0]):
            for c in range(piece.shape[1]):
                if piece[r, c] == 1:
                    b[row + r, col + c] = 1
        return self._clear_lines(b)

    def _count_holes(self, board):
        holes = 0
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if board[r, c] == 0:
                    up = (r == 0) or (board[r-1, c] != 0)
                    down = (r == self.grid_size - 1) or (board[r+1, c] != 0)
                    left = (c == 0) or (board[r, c-1] != 0)
                    right = (c == self.grid_size - 1) or (board[r, c+1] != 0)
                    if up and down and left and right:
                        holes += 1
        return holes
    
    def find_best_sequence(self, board, pieces):
        """Tìm chuỗi 3 nước đi tốt nhất (từ code gốc)"""
        indexed_pieces = list(enumerate(pieces))
        best_sequence = []
        best_total_score = -1

        for permutation in itertools.permutations(indexed_pieces):
            current_board = board.copy()
            current_sequence = []
            current_total_score = 0
            
            for original_index, piece in permutation:
                best_move = self.solve_with_heuristics(current_board, [piece])
                if best_move:
                    current_board = best_move['board_after']
                    current_total_score += best_move['score']
                    current_sequence.append({
                        'piece': best_move['piece_used'],
                        'position': best_move['position'],
                        'score': best_move['score'],
                        'piece_index': original_index
                    })

            if current_total_score > best_total_score:
                best_total_score = current_total_score
                best_sequence = current_sequence

        return best_sequence[:3]

# =============================================================================
# COPILOT GUI
# =============================================================================
class CopilotGUI:
    """GUI Copilot Mode - Tự động chụp, gen solutions, đợi, lặp lại"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Block Blast Copilot")
        self.root.geometry("1000x750")
        self.root.configure(bg="#1e1e2e")
        
        self.screen_capture = ScreenCapture()
        self.vision = BlockBlastVision(8)
        self.pieces_extractor = PiecesExtractor(self.vision)
        self.solver = BlockBlastSolver(8)
        
        self.is_running = False
        self.copilot_thread = None
        self.wait_seconds = 8  # Thời gian đợi user chơi
        self.temp_image_path = "temp_capture.png"
        
        self.current_board = None
        self.current_pieces = None
        self.current_solutions = []
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg="#1e1e2e")
        header.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(header, text="🤖 Block Blast Copilot", font=("Segoe UI", 24, "bold"), 
                fg="#89b4fa", bg="#1e1e2e").pack()
        
        # Control Panel
        control = tk.Frame(self.root, bg="#313244", relief=tk.RAISED, bd=2)
        control.pack(fill=tk.X, padx=20, pady=10)
        control_inner = tk.Frame(control, bg="#313244")
        control_inner.pack(padx=15, pady=12)
        
        # Start/Stop Button
        self.start_btn = tk.Button(control_inner, text="▶ START COPILOT", 
                                   font=("Segoe UI", 14, "bold"), bg="#a6e3a1", 
                                   fg="#1e1e2e", relief=tk.FLAT, bd=0, padx=30, pady=12,
                                   cursor="hand2", command=self.toggle_copilot)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        # Manual Capture Button
        self.manual_btn = tk.Button(control_inner, text="📸 SETUP REGION", 
                                    font=("Segoe UI", 11), bg="#89b4fa", 
                                    fg="#1e1e2e", relief=tk.FLAT, bd=0, padx=20, pady=10,
                                    cursor="hand2", command=self.setup_region_interactive)
        self.manual_btn.pack(side=tk.LEFT, padx=5)
        
        # Status Display
        status_frame = tk.Frame(self.root, bg="#313244", relief=tk.RAISED, bd=2)
        status_frame.pack(fill=tk.X, padx=20, pady=5)
        status_inner = tk.Frame(status_frame, bg="#313244")
        status_inner.pack(padx=15, pady=8)
        
        self.status_label = tk.Label(status_inner, text="⏸ Idle - Click SETUP REGION để bắt đầu", 
                                     font=("Segoe UI", 12, "bold"), 
                                     fg="#cdd6f4", bg="#313244")
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.countdown_label = tk.Label(status_inner, text="", 
                                       font=("Segoe UI", 11), 
                                       fg="#f9e2af", bg="#313244")
        self.countdown_label.pack(side=tk.LEFT, padx=10)
        
        # Content Area (2 columns: Left=Board+Pieces vertical, Right=Solutions horizontal)
        content = tk.Frame(self.root, bg="#1e1e2e")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # ===== LEFT COLUMN: Board + Pieces (VERTICAL) =====
        left_column = tk.Frame(content, bg="#1e1e2e")
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # Board (top of left column)
        board_frame = tk.Frame(left_column, bg="#313244", relief=tk.RAISED, bd=2)
        board_frame.pack(fill=tk.BOTH, padx=5, pady=(0, 10))
        
        tk.Label(board_frame, text="Board", font=("Segoe UI", 12, "bold"), 
                fg="#cdd6f4", bg="#313244").pack(pady=5)
        
        self.board_label = tk.Label(board_frame, text="No board", 
                                    font=("Segoe UI", 10), fg="#6c7086", 
                                    bg="#1e1e2e", width=25, height=15)
        self.board_label.pack(padx=10, pady=10)
        
        # Pieces (bottom of left column)
        pieces_frame = tk.Frame(left_column, bg="#313244", relief=tk.RAISED, bd=2)
        pieces_frame.pack(fill=tk.BOTH, padx=5)
        
        tk.Label(pieces_frame, text="Pieces", font=("Segoe UI", 12, "bold"), 
                fg="#cdd6f4", bg="#313244").pack(pady=5)
        
        pieces_container = tk.Frame(pieces_frame, bg="#313244")
        pieces_container.pack(fill=tk.BOTH, padx=5, pady=5)
        
        self.piece_labels = []
        for i in range(3):
            lbl = tk.Label(pieces_container, text=f"P{i+1}", font=("Segoe UI", 9), 
                          fg="#6c7086", bg="#1e1e2e", height=4)
            lbl.pack(fill=tk.X, padx=5, pady=3)
            self.piece_labels.append(lbl)
        
        # ===== RIGHT SIDE: Solutions (3 columns HORIZONTAL) =====
        right = tk.Frame(content, bg="#1e1e2e")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        tk.Label(right, text="💡 Solutions", font=("Segoe UI", 14, "bold"), 
                fg="#a6e3a1", bg="#1e1e2e").pack(pady=(0, 10))
        
        # Container cho 3 solutions
        solutions_container = tk.Frame(right, bg="#1e1e2e")
        solutions_container.pack(fill=tk.BOTH, expand=True)
        
        self.sol_labels = []
        for i in range(3):
            # Mỗi solution là 1 cột
            sol_col = tk.Frame(solutions_container, bg="#313244", relief=tk.RAISED, bd=2)
            sol_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 5, 0))
            
            # Title
            title_frame = tk.Frame(sol_col, bg="#45475a")
            title_frame.pack(fill=tk.X)
            tk.Label(title_frame, text=f"Solution {i+1}", 
                    font=("Segoe UI", 11, "bold"), 
                    fg="#a6e3a1", bg="#45475a").pack(pady=5)
            
            # Image label
            lbl = tk.Label(sol_col, text="Waiting...", font=("Segoe UI", 9), 
                          fg="#6c7086", bg="#1e1e2e")
            lbl.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            
            self.sol_labels.append(lbl)
    
    def setup_region_interactive(self):
        """Setup vùng game - cho user chọn 2 vùng riêng biệt"""
        msg = messagebox.askquestion("Setup Region", 
            "Sẵn sàng chụp màn hình?\n\n"
            "Chúng ta sẽ thực hiện 2 bước:\n"
            "1. Chọn vùng BOARD (lưới 8x8)\n"
            "2. Chọn vùng PIECES (khu vực chứa 3 khối)\n\n"
            "Click YES để bắt đầu.")
        
        if msg != 'yes':
            return
        
        # Chụp toàn màn hình
        self.update_status("📸 Capturing full screen...")
        full_img = self.screen_capture.capture_full_screen()
        
        if full_img is None:
            messagebox.showerror("Lỗi", "Không thể chụp màn hình!")
            return
        
        # Tạo dialog để user chọn vùng
        self.show_dual_region_selector(full_img)
    
    def show_dual_region_selector(self, full_img):
        """Hiển thị dialog để user chọn 2 vùng tuần tự"""
        selector = tk.Toplevel(self.root)
        selector.title("Select Game Regions")
        selector.attributes('-topmost', True)
        
        # Convert image
        img_rgb = cv2.cvtColor(full_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        
        # Resize
        screen_w = selector.winfo_screenwidth()
        screen_h = selector.winfo_screenheight()
        scale = min((screen_w - 100) / pil_img.width, (screen_h - 100) / pil_img.height, 1.0)
        
        display_w = int(pil_img.width * scale)
        display_h = int(pil_img.height * scale)
        display_img = pil_img.resize((display_w, display_h), Image.Resampling.LANCZOS)
        
        # Wrapper frame
        frame = tk.Frame(selector)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas
        canvas = tk.Canvas(frame, width=display_w, height=display_h, cursor="cross")
        canvas.pack(padx=10, pady=10)
        
        photo = ImageTk.PhotoImage(display_img)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo
        
        # Instructions Label
        self.instr_var = tk.StringVar(value="BƯỚC 1/2: Kéo chuột bao quanh vùng BOARD (lưới 8x8)")
        lbl_instr = tk.Label(frame, textvariable=self.instr_var, 
                             font=("Segoe UI", 12, "bold"), fg="#dc2626", bg="white")
        lbl_instr.pack(pady=5)
        
        # State
        state = {
            'step': 1, # 1=Board, 2=Pieces
            'start_x': None, 'start_y': None, 'rect': None,
            'board_rect': None
        }
        
        def on_mouse_down(event):
            state['start_x'] = event.x
            state['start_y'] = event.y
            if state['rect']:
                canvas.delete(state['rect'])
                state['rect'] = None
        
        def on_mouse_drag(event):
            if state['start_x'] is not None:
                if state['rect']:
                    canvas.delete(state['rect'])
                color = '#00ff00' if state['step'] == 1 else '#00ffff'
                state['rect'] = canvas.create_rectangle(
                    state['start_x'], state['start_y'],
                    event.x, event.y,
                    outline=color, width=3
                )
        
        def on_confirm():
            if not state['rect']:
                messagebox.showwarning("Warning", "Vui lòng chọn vùng trước!")
                return
                
            # Lấy tọa độ
            coords = canvas.coords(state['rect'])
            x1, y1, x2, y2 = coords
            
            # Convert về tọa độ gốc
            orig_x1 = int(x1 / scale)
            orig_y1 = int(y1 / scale)
            orig_x2 = int(x2 / scale)
            orig_y2 = int(y2 / scale)
            
            x = min(orig_x1, orig_x2)
            y = min(orig_y1, orig_y2)
            w = abs(orig_x2 - orig_x1)
            h = abs(orig_y2 - orig_y1)
            
            if state['step'] == 1:
                # Xong bước 1: Save Board Region
                self.screen_capture.set_board_region(x, y, w, h)
                
                # Vẽ lại rect màu cố định để đánh dấu đã chọn
                canvas.create_rectangle(x1, y1, x2, y2, outline='#00aa00', width=2, dash=(4, 4))
                canvas.delete(state['rect'])
                state['rect'] = None
                
                # Chuyển sang bước 2
                state['step'] = 2
                self.instr_var.set("BƯỚC 2/2: Kéo chuột bao quanh vùng PIECES (3 khối ở dưới)")
                lbl_instr.configure(fg="#0284c7") # Đổi màu text
                
            else:
                # Xong bước 2: Save Pieces Region
                self.screen_capture.set_pieces_region(x, y, w, h)
                
                self.update_status("✅ Setup Regions OK!")
                selector.destroy()
                
                # Test capture & display
                self.test_regions()
        
        canvas.bind("<Button-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        
        tk.Button(frame, text="✓ CONFIRM", font=("Segoe UI", 12, "bold"),
                 bg="#16a34a", fg="white", command=on_confirm, padx=20, pady=10).pack(pady=10)

    def test_regions(self):
        """Test chụp và hiển thị ngay sau khi setup"""
        try:
            b_img = self.screen_capture.capture_board("temp_board.png")
            p_img = self.screen_capture.capture_pieces("temp_pieces.png")
            
            if b_img is not None and p_img is not None:
                self.current_board = self.vision.extract_board_from_image("temp_board.png")
                self.current_pieces = self.pieces_extractor.extract_pieces_from_crop("temp_pieces.png")
                self.display_board_and_pieces()
                messagebox.showinfo("Success", "Đã setup thành công Board & Pieces!")
            else:
                messagebox.showerror("Lỗi", "Test capture failed!")
        except Exception as e:
            print(e)
            messagebox.showerror("Lỗi", f"Error testing regions: {e}")

    def toggle_copilot(self):
        """Bật/tắt Copilot Mode"""
        if not self.is_running:
            if not self.screen_capture.board_region or not self.screen_capture.pieces_region:
                messagebox.showerror("Lỗi", "Vui lòng setup vùng game trước!")
                return
            self.start_copilot()
        else:
            self.stop_copilot()
    
    def start_copilot(self):
        """Bắt đầu Copilot Mode"""
        self.is_running = True
        self.start_btn.configure(text="⏸ STOP COPILOT", bg="#f38ba8")
        self.update_status("▶ Running")
        
        # Chạy copilot loop trong thread riêng
        self.copilot_thread = threading.Thread(target=self.copilot_loop, daemon=True)
        self.copilot_thread.start()
    
    def stop_copilot(self):
        """Dừng Copilot Mode"""
        self.is_running = False
        self.start_btn.configure(text="▶ START COPILOT", bg="#a6e3a1")
        self.update_status("⏸ Stopped")
        self.countdown_label.configure(text="")
    
    def copilot_loop(self):
        """Vòng lặp chính của Copilot"""
        while self.is_running:
            try:
                # 1. Chụp màn hình (Board & Pieces)
                self.update_status("📸 Capturing...")
                
                # Capture Board
                board_img = self.screen_capture.capture_board("temp_board.png")
                if board_img is None:
                    self.update_status("❌ Capture Board failed")
                    time.sleep(2)
                    continue
                    
                # Capture Pieces
                pieces_img = self.screen_capture.capture_pieces("temp_pieces.png")
                if pieces_img is None:
                    self.update_status("❌ Capture Pieces failed")
                    time.sleep(2)
                    continue
                
                # 2. Đọc board và pieces
                self.update_status("🔍 Analyzing...")
                self.current_board = self.vision.extract_board_from_image("temp_board.png")
                
                # Dùng method mới cho pieces crop
                self.current_pieces = self.pieces_extractor.extract_pieces_from_crop("temp_pieces.png")
                
                # 3. Hiển thị board và pieces
                self.root.after(0, self.display_board_and_pieces)
                
                # 4. Tìm chuỗi 3 nước đi tuần tự (sequential guidance)
                self.update_status("💡 Finding sequential solutions...")
                self.current_solutions = []
                
                # Sử dụng find_best_sequence để tìm thứ tự tối ưu
                best_sequence = self.solver.find_best_sequence(self.current_board, self.current_pieces)
                
                # Lưu solutions với board state tương ứng
                simulated_board = self.current_board.copy()
                for move in best_sequence:
                    if move:
                        # Lưu solution với board state TRƯỚC KHI đặt piece
                        self.current_solutions.append({
                            'piece': move['piece'],
                            'position': move['position'],
                            'score': move['score'],
                            'piece_index': move['piece_index'],
                            'board_state': simulated_board.copy()  # Board state cho solution này
                        })
                        # Cập nhật board cho solution tiếp theo
                        simulated_board = self.solver._place_and_clear(
                            simulated_board, move['piece'], *move['position']
                        )
                    else:
                        self.current_solutions.append(None)
                
                # Đảm bảo có đủ 3 solutions
                while len(self.current_solutions) < 3:
                    self.current_solutions.append(None)
                
                # 5. Hiển thị solutions
                self.root.after(0, self.display_solutions)
                
                # 6. Đợi user chơi
                self.update_status(f"⏳ Waiting for you to play...")
                for remaining in range(self.wait_seconds, 0, -1):
                    if not self.is_running:
                        break
                    self.root.after(0, lambda r=remaining: 
                                  self.countdown_label.configure(text=f"Next: {r}s"))
                    time.sleep(1)
                
            except Exception as e:
                print(f"Lỗi trong copilot loop: {e}")
                import traceback
                traceback.print_exc()
                self.update_status(f"❌ Error: {e}")
                time.sleep(2)

    

    def display_board_and_pieces(self):

        """Hiển thị board và pieces"""

        # Board - 220px như code gốc

        if self.current_board is not None:

            img = self.create_board_image(self.current_board)

            max_size = 220

            w0, h0 = img.size

            ratio = min(max_size / w0, max_size / h0)

            img = img.resize((int(w0 * ratio), int(h0 * ratio)), Image.Resampling.LANCZOS)

            ph = ImageTk.PhotoImage(img)

            self.board_label.configure(image=ph, text="")

            self.board_label.image = ph

        

        # Pieces - 60px như code gốc

        if self.current_pieces:

            for i, piece in enumerate(self.current_pieces[:3]):

                img = self.create_piece_image(piece, cell_size=30)

                max_size = 60

                w0, h0 = img.size

                if w0 == 0 or h0 == 0: continue

                ratio = min(max_size / w0, max_size / h0)

                img = img.resize((int(w0 * ratio), int(h0 * ratio)), Image.Resampling.LANCZOS)

                ph = ImageTk.PhotoImage(img)

                self.piece_labels[i].configure(image=ph, text="")
                self.piece_labels[i].image = ph
    
    def display_solutions(self):
        """Hiển thị solutions tuần tự - mỗi solution trên board state tương ứng"""
        for i, sol in enumerate(self.current_solutions[:3]):
            if sol and 'piece' in sol:
                # Sử dụng board_state riêng của mỗi solution
                board_to_use = sol.get('board_state', self.current_board)
                img = self.create_solution_image(
                    board_to_use,  # Board state cho solution này
                    sol['piece'], 
                    sol['position']
                )
                # 150px như code gốc (không phải 220px)
                max_size = 150
                w0, h0 = img.size
                ratio = min(max_size / w0, max_size / h0)
                img = img.resize((int(w0 * ratio), int(h0 * ratio)), Image.Resampling.LANCZOS)
                ph = ImageTk.PhotoImage(img)
                self.sol_labels[i].configure(image=ph, text="")
                self.sol_labels[i].image = ph
            else:
                self.sol_labels[i].configure(text="No solution", image="")
    
    def update_status(self, text: str):
        """Cập nhật status label"""
        self.root.after(0, lambda: self.status_label.configure(text=text))


    def create_board_image(self, board):

        """Tạo ảnh board"""

        h, w = board.shape

        cell = 50

        base = np.ones((h * cell, w * cell, 3), dtype=np.uint8) * 30

        for r in range(h):

            for c in range(w):

                color = (50, 50, 50) if board[r, c] == 0 else (100, 180, 100)

                y1, x1 = r * cell, c * cell

                y2, x2 = (r + 1) * cell, (c + 1) * cell

                base[y1:y2, x1:x2] = color

                cv2.rectangle(base, (x1, y1), (x2-1, y2-1), (80, 80, 80), 1)

        return Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB))

    

    def create_piece_image(self, piece, cell_size=25):

        """Tạo ảnh piece - cell_size nhỏ hơn"""

        h, w = piece.shape

        base = np.ones((h * cell_size, w * cell_size, 3), dtype=np.uint8) * 30

        for r in range(h):

            for c in range(w):

                color = (50, 50, 50) if piece[r, c] == 0 else (100, 180, 100)

                y1, x1 = r * cell_size, c * cell_size

                y2, x2 = (r + 1) * cell_size, (c + 1) * cell_size

                base[y1:y2, x1:x2] = color

                cv2.rectangle(base, (x1, y1), (x2-1, y2-1), (80, 80, 80), 1)

        return Image.fromarray(base)

    

    def create_solution_image(self, board, piece, pos):

        """Tạo ảnh solution với highlight"""

        b = board.copy()

        r0, c0 = pos

        for r in range(piece.shape[0]):

            for c in range(piece.shape[1]):

                if piece[r, c] == 1:

                    br, bc = r0 + r, c0 + c

                    if 0 <= br < b.shape[0] and 0 <= bc < b.shape[1]:

                        b[br, bc] = 9

        

        h, w = b.shape

        cell = 50

        base = np.ones((h * cell, w * cell, 3), dtype=np.uint8) * 30

        for r in range(h):

            for c in range(w):

                if b[r, c] == 0:

                    color = (50, 50, 50)

                elif b[r, c] == 9:

                    color = (100, 200, 255)  # Highlight xanh dương

                else:

                    color = (100, 180, 100)

                y1, x1 = r * cell, c * cell

                y2, x2 = (r + 1) * cell, (c + 1) * cell

                base[y1:y2, x1:x2] = color

                cv2.rectangle(base, (x1, y1), (x2-1, y2-1), (80, 80, 80), 1)

        return Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB))

    

    def run(self):

        self.root.mainloop()



def main():

    print("=== BLOCK BLAST COPILOT MODE ===")

    print("Tích hợp vision logic từ code gốc")

    print("Chỉ setup 1 lần, sau đó tự động chụp mỗi 8s")

    app = CopilotGUI()

    app.run()



if __name__ == "__main__":

    main()

