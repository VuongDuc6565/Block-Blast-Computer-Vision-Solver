# Fix script - chạy để sửa lỗi UI layout
import re

# Đọc file
with open('block_blast_copilot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Tìm và thay thế phần create_widgets bị lỗi
old_section = r'''        self.status_label.pack\(side=tk.LEFT, padx=10\)
        
        solutions_container = tk.Frame\(right, bg="#1e1e2e"\)'''

new_section = '''        self.status_label.pack(side=tk.LEFT, padx=10)
        
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
        solutions_container = tk.Frame(right, bg="#1e1e2e")'''

content = re.sub(old_section, new_section, content, flags=re.DOTALL)

# Lưu lại
with open('block_blast_copilot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed!")
