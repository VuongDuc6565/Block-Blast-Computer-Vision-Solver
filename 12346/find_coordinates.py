# -*- coding: utf-8 -*-
"""
Coordinate Finder - Công cụ tìm tọa độ vùng game
Chạy file này để tìm tọa độ chính xác cho game của bạn
"""
import tkinter as tk
from tkinter import messagebox
from mss import mss
from PIL import Image, ImageTk, ImageDraw
import numpy as np

class CoordinateFinder:
    """Tool để tìm tọa độ vùng game"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Block Blast - Coordinate Finder")
        self.root.geometry("800x600")
        
        self.sct = mss()
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Instructions
        tk.Label(self.root, text="🎯 Coordinate Finder", 
                font=("Arial", 20, "bold")).pack(pady=10)
        
        instructions = """
        Hướng dẫn:
        1. Click "Capture Full Screen" để chụp toàn màn hình
        2. Click và kéo chuột để chọn vùng game
        3. Tọa độ sẽ hiển thị bên dưới
        4. Copy tọa độ và paste vào code
        """
        tk.Label(self.root, text=instructions, font=("Arial", 10), 
                justify=tk.LEFT).pack(pady=10)
        
        # Capture button
        tk.Button(self.root, text="📸 Capture Full Screen", 
                 font=("Arial", 14, "bold"), bg="#4CAF50", fg="white",
                 command=self.capture_screen, padx=20, pady=10).pack(pady=10)
        
        # Canvas for image
        self.canvas = tk.Canvas(self.root, bg="gray", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Coordinates display
        self.coord_frame = tk.Frame(self.root, bg="#f0f0f0", relief=tk.RAISED, bd=2)
        self.coord_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.coord_label = tk.Label(self.coord_frame, 
                                    text="Chưa chọn vùng", 
                                    font=("Courier", 11, "bold"),
                                    bg="#f0f0f0")
        self.coord_label.pack(pady=10)
        
        # Copy button
        self.copy_btn = tk.Button(self.coord_frame, text="📋 Copy Code", 
                                 font=("Arial", 10), bg="#2196F3", fg="white",
                                 command=self.copy_coordinates, state=tk.DISABLED)
        self.copy_btn.pack(pady=5)
        
    def capture_screen(self):
        """Chụp toàn màn hình"""
        # Get primary monitor
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        # Resize to fit canvas
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Calculate scale
            scale = min(canvas_width / img.width, canvas_height / img.height)
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            
            self.display_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.original_img = img
            self.scale = scale
            
            # Display
            self.photo = ImageTk.PhotoImage(self.display_img)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            messagebox.showinfo("Success", "Đã chụp màn hình!\nBây giờ hãy click và kéo để chọn vùng game.")
    
    def on_mouse_down(self, event):
        """Bắt đầu chọn vùng"""
        self.start_x = event.x
        self.start_y = event.y
        
    def on_mouse_drag(self, event):
        """Kéo để chọn vùng"""
        if self.start_x is not None:
            # Clear previous rectangle
            self.canvas.delete("selection")
            
            # Draw new rectangle
            self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline="red", width=3, tags="selection"
            )
    
    def on_mouse_up(self, event):
        """Hoàn thành chọn vùng"""
        if self.start_x is not None:
            self.end_x = event.x
            self.end_y = event.y
            
            # Convert to original coordinates
            orig_x1 = int(self.start_x / self.scale)
            orig_y1 = int(self.start_y / self.scale)
            orig_x2 = int(self.end_x / self.scale)
            orig_y2 = int(self.end_y / self.scale)
            
            # Ensure x1 < x2 and y1 < y2
            x = min(orig_x1, orig_x2)
            y = min(orig_y1, orig_y2)
            width = abs(orig_x2 - orig_x1)
            height = abs(orig_y2 - orig_y1)
            
            # Display coordinates
            coord_text = f"""
Tọa độ vùng game:
x = {x}
y = {y}
width = {width}
height = {height}

Code để paste:
self.screen_capture.set_game_region(
    x={x},
    y={y},
    width={width},
    height={height}
)
            """
            self.coord_label.configure(text=coord_text)
            self.copy_btn.configure(state=tk.NORMAL)
            
            # Store for copying
            self.current_coords = f"self.screen_capture.set_game_region(x={x}, y={y}, width={width}, height={height})"
    
    def copy_coordinates(self):
        """Copy tọa độ vào clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_coords)
        messagebox.showinfo("Copied", "Đã copy code vào clipboard!\nPaste vào hàm setup_region() trong block_blast_copilot.py")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    print("=== COORDINATE FINDER ===")
    print("Tool này giúp bạn tìm tọa độ chính xác cho vùng game")
    app = CoordinateFinder()
    app.run()
