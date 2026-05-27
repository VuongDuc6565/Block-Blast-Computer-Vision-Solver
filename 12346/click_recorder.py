"""
CLICK RECORDER - Ghi lại vị trí click chuột
"""
import time
import json
from pynput import mouse

positions = []

def on_click(x, y, button, pressed):
    global positions
    
    if pressed and button == mouse.Button.left:
        positions.append((x, y))
        print(f"Click {len(positions)}: Position ({x}, {y})")
        
        if len(positions) == 3:
            return False

def main():
    global positions
    
    print("="*60)
    print("CLICK RECORDER - Ghi lại vị trí click chuột")
    print("="*60)
    print("\nHướng dẫn:")
    print("1. Click vào BLOCK ĐẦU TIÊN (bên trái)")
    print("2. Click vào BLOCK THỨ HAI (ở giữa)")
    print("3. Click vào BLOCK THỨ BA (bên phải)")
    print("\n⚠️  Đảm bảo game đang mở và hiển thị!")
    print("="*60)
    
    input("\nNhấn Enter để bắt đầu ghi...")
    
    print("\n🔴 Đang ghi... Click vào 3 block theo thứ tự!")
    
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
    
    if len(positions) == 3:
        print("\n✅ Got 3 positions!")
        print("\nVị trí đã ghi:")
        for i, pos in enumerate(positions):
            print(f"  Block {i}: {pos}")
        
        # Update config
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {}
            
        config["block_positions_manual"] = positions
        
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
        
        print("\n✅ Đã lưu vào config.json!")
        print("Bây giờ hãy chạy: python smart_bot.py")

if __name__ == "__main__":
    main()
