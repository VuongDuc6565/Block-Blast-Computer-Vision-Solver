# Block Blast Copilot - Quick Start Guide

## 🚀 Cách sử dụng (Đã cập nhật)

### Bước 1: Mở game
- Mở **Block Blast Gem Find Puzzle** trên trình duyệt
- Đảm bảo game hiển thị đầy đủ trên màn hình

### Bước 2: Chạy Copilot
```bash
python block_blast_copilot.py
```

### Bước 3: Setup vùng game (CHỈ 1 LẦN)
1. Click nút **"📸 SETUP REGION"**
2. Click **YES** để chụp toàn màn hình
3. **Kéo chuột** để chọn vùng game (viền xanh lá)
4. Click **"✓ Confirm Selection"**
5. Kiểm tra board và pieces hiển thị đúng

### Bước 4: Bắt đầu Copilot
1. Click **"▶ START COPILOT"**
2. Hệ thống sẽ:
   - Tự động chụp màn hình mỗi 8 giây
   - Phân tích board và 3 pieces
   - Hiển thị 3 solutions (highlight màu xanh)
   - Đợi 8 giây để bạn chơi
   - Lặp lại tự động

### Bước 5: Chơi theo gợi ý
- Xem 3 solutions được highlight
- Đặt pieces vào vị trí gợi ý
- Copilot sẽ tự động chụp lại sau 8 giây

### Bước 6: Dừng khi muốn
- Click **"⏸ STOP COPILOT"** để dừng

## ✨ Tính năng mới

### ✅ Interactive Region Selector
- Chụp toàn màn hình
- Click-drag để chọn vùng game chính xác
- Tự động test và hiển thị board/pieces
- Lưu tọa độ để dùng cho auto-capture

### ✅ Fixed Threading Error
- Sửa lỗi `_thread._local` với `mss`
- Tạo instance mới mỗi lần chụp
- Ổn định hơn khi chạy trong thread

### ✅ Vision Logic từ Code Gốc
- `BlockBlastVision`: Đọc board chính xác
- `PiecesExtractor`: Valley projection cho pieces
- `BlockBlastSolver`: Tìm chuỗi 3 nước đi tối ưu

## 🎨 UI Features

- **Dark theme** dễ nhìn
- **3 cột**: Board | Pieces | Solutions
- **Real-time countdown**: Hiển thị thời gian còn lại
- **Status indicator**: Biết đang làm gì
- **Green highlight**: Solutions rõ ràng

## 🐛 Troubleshooting

### Không chụp được màn hình
- Đảm bảo game đang mở
- Thử chọn lại vùng game

### Board/Pieces không đúng
- Chọn lại vùng game chính xác hơn
- Đảm bảo chọn đúng vùng chứa board và pieces

### Solutions không tốt
- Đây là thuật toán từ code gốc
- Có thể điều chỉnh solver nếu cần

## ⚙️ Tùy chỉnh

### Thay đổi thời gian đợi
Trong code, dòng 513:
```python
self.wait_seconds = 8  # Đổi thành 7, 9, 10...
```

### Debug
Xem console để theo dõi:
- Board detection
- Pieces extraction
- Solutions finding
