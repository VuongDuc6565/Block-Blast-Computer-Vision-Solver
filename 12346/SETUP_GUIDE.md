# Block Blast Copilot - Setup Guide

## ⚠️ QUAN TRỌNG: Chọn vùng đúng

### Vùng cần chọn phải bao gồm:
```
┌─────────────────────┐
│                     │
│   BOARD (8x8)       │  ← Phần board
│                     │
├─────────────────────┤
│  [P1]  [P2]  [P3]   │  ← 3 Pieces
└─────────────────────┘
```

**ĐÚNG** ✅:
- Chọn từ trên cùng của board
- Xuống đến hết 3 pieces ở dưới
- Bao gồm toàn bộ chiều rộng

**SAI** ❌:
- Chỉ chọn board (thiếu pieces)
- Chọn quá hẹp (cắt mất pieces)

## 🚀 Hướng dẫn Setup

### Bước 1: Mở game
- Mở Block Blast trên trình duyệt
- Đảm bảo hiển thị đầy đủ board + 3 pieces

### Bước 2: Chạy Copilot
```bash
python block_blast_copilot.py
```

### Bước 3: Setup Region
1. Click **"📸 SETUP REGION"**
2. Click **YES**
3. **Kéo chuột** chọn vùng:
   - Từ **trên cùng board**
   - Đến **dưới cùng 3 pieces**
4. Click **"✓ Confirm Selection"**

### Bước 4: Kiểm tra
Sau khi confirm, xem console:
```
=== PIECES EXTRACTION ===
Found 3 piece boxes  ← Phải thấy 3 boxes
Piece 1: Grid (2, 3), filled cells: 6
Piece 2: Grid (1, 4), filled cells: 4
Piece 3: Grid (3, 3), filled cells: 9
Extracted 3 pieces
```

**Nếu thấy "Found 0 piece boxes"**:
- ❌ Vùng chọn chưa đúng
- 🔄 Click "SETUP REGION" lại
- ✅ Chọn vùng rộng hơn, bao gồm cả pieces

### Bước 5: Start Copilot
- Click **"▶ START COPILOT"**
- Xem 3 solutions hiển thị
- Chơi theo gợi ý

## 🐛 Troubleshooting

### "Found 0 piece boxes"
**Nguyên nhân**: Vùng chọn không bao gồm pieces

**Giải pháp**:
1. Click "SETUP REGION" lại
2. Chọn vùng lớn hơn
3. Đảm bảo thấy cả board VÀ 3 pieces trong vùng chọn

### Pieces hiển thị sai
**Nguyên nhân**: Pieces bị che khuất hoặc màu sắc khác

**Giải pháp**:
- Đảm bảo pieces có màu rõ ràng
- Không bị che bởi popup/menu

### Board đọc đúng nhưng không có solutions
**Nguyên nhân**: Pieces không được đọc

**Giải pháp**:
- Kiểm tra console xem "Found X piece boxes"
- Nếu X = 0, setup lại region

## 📊 Debug Output

Khi chạy, console sẽ hiển thị:

```
=== DEBUG BOARD ===
Row 0: ........
Row 1: 5411111.
...
Fill ratio: 45.3%

=== PIECES EXTRACTION ===
Found 3 piece boxes
Piece 1: Grid (3, 2), filled cells: 5
Piece 2: Grid (2, 2), filled cells: 4
Piece 3: Grid (1, 4), filled cells: 4
Extracted 3 pieces
```

**Kiểm tra**:
- ✅ Fill ratio > 0% → Board OK
- ✅ Found 3 piece boxes → Pieces OK
- ✅ Filled cells > 0 → Pieces có dữ liệu

## 💡 Tips

1. **Chọn vùng rộng hơn** thay vì hẹp
2. **Bao gồm toàn bộ** board + pieces
3. **Kiểm tra console** để debug
4. **Thử lại** nếu không thấy pieces
