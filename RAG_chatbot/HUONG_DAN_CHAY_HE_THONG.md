# 🚀 HƯỚNG DẪN CHẠY HỆ THỐNG ĐẦY ĐỦ

## 📋 Tổng quan

Hệ thống gồm 2 phần:
- **Backend**: Flask API server (RAG Chatbot) - Port 5000
- **Frontend**: HTML/JS (assistant.html) - Cần web server để tránh CORS

## ⚙️ CHUẨN BỊ (Chỉ cần làm 1 lần)

### Bước 1: Cài đặt dependencies cho Backend

```powershell
cd "Backend\RAG_chatbot"
pip install -r requirements.txt
```

### Bước 2: Kiểm tra setup Backend

```powershell
python check_setup.py
```

**Kết quả mong đợi:** Tất cả đều ✅ PASS

### Bước 3: Chuẩn bị dữ liệu (Nếu chưa có)

```powershell
# Chỉ cần chạy lần đầu hoặc khi có dữ liệu mới
python scripts\index_mongo.py
python scripts\embed_bge_m3.py
```

---

## 🚀 CÁCH CHẠY HỆ THỐNG

### CÁCH 1: Chạy thủ công (Khuyến nghị)

#### Bước 1: Chạy Backend API Server

Mở **Terminal/PowerShell thứ nhất**:

```powershell
cd "Backend\RAG_chatbot"
python app.py
```

**Kết quả mong đợi:**
```
Starting RAG Chatbot API server...
Loading RAG retriever and Gemini model...
Loaded 1234 embeddings into RAM for RAG.
✅ RAG retriever and Gemini model loaded successfully!
 * Running on http://0.0.0.0:5000
```

**⚠️ LƯU Ý:** Giữ terminal này mở, không đóng!

#### Bước 2: Chạy Frontend Web Server

Mở **Terminal/PowerShell thứ hai** (terminal mới):

**Option A: Dùng Python HTTP Server (Đơn giản nhất)**

```powershell
cd "Frontend"
python -m http.server 8000
```

**Option B: Dùng Node.js http-server (Nếu có Node.js)**

```powershell
cd "Frontend"
npx http-server -p 8000
```

**Kết quả mong đợi:**
```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

#### Bước 3: Mở Browser

Mở browser và truy cập:
```
http://localhost:8000/assistant.html
```

**Hoặc:**
```
http://127.0.0.1:8000/assistant.html
```

---

### CÁCH 2: Dùng script tự động (Windows)

Tạo file `start_system.bat` trong thư mục gốc dự án:

```batch
@echo off
echo ========================================
echo Starting RAG Chatbot System
echo ========================================
echo.

echo [1/3] Starting Backend API Server...
start "Backend API" cmd /k "cd Backend\RAG_chatbot && python app.py"

timeout /t 5 /nobreak >nul

echo [2/3] Starting Frontend Web Server...
start "Frontend Server" cmd /k "cd Frontend && python -m http.server 8000"

timeout /t 3 /nobreak >nul

echo [3/3] Opening browser...
start http://localhost:8000/assistant.html

echo.
echo ========================================
echo System started!
echo ========================================
echo Backend API: http://localhost:5000
echo Frontend: http://localhost:8000/assistant.html
echo.
echo Press any key to exit (servers will keep running)...
pause >nul
```

**Cách dùng:**
1. Double-click file `start_system.bat`
2. Đợi vài giây để hệ thống khởi động
3. Browser sẽ tự động mở

---

### CÁCH 3: Dùng PowerShell script

Tạo file `start_system.ps1`:

```powershell
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting RAG Chatbot System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Backend
Write-Host "[1/3] Starting Backend API Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'Backend\RAG_chatbot'; python app.py"

Start-Sleep -Seconds 5

# Start Frontend
Write-Host "[2/3] Starting Frontend Web Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'Frontend'; python -m http.server 8000"

Start-Sleep -Seconds 3

# Open Browser
Write-Host "[3/3] Opening browser..." -ForegroundColor Yellow
Start-Process "http://localhost:8000/assistant.html"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "System started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Backend API: http://localhost:5000" -ForegroundColor White
Write-Host "Frontend: http://localhost:8000/assistant.html" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit (servers will keep running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

**Cách dùng:**
```powershell
.\start_system.ps1
```

---

## ✅ KIỂM TRA HỆ THỐNG ĐÃ CHẠY ĐÚNG

### 1. Kiểm tra Backend

Mở browser và truy cập:
```
http://localhost:5000/api/health
```

**Kết quả mong đợi:**
```json
{
  "status": "ok",
  "message": "RAG Chatbot API is running"
}
```

### 2. Kiểm tra Frontend

Mở browser và truy cập:
```
http://localhost:8000/assistant.html
```

**Kết quả mong đợi:**
- Trang assistant.html hiển thị bình thường
- Có thể nhập câu hỏi và gửi

### 3. Test Chat

1. Mở `http://localhost:8000/assistant.html`
2. Nhập câu hỏi: "thầy Phùng Ngọc Tùng dạy cái gì"
3. Nhấn Enter hoặc click nút gửi
4. Đợi vài giây
5. Phải thấy câu trả lời từ AI

---

## 🐛 XỬ LÝ LỖI

### Lỗi: "Failed to fetch" hoặc "Connection refused"

**Nguyên nhân:** Backend API chưa chạy

**Giải pháp:**
1. Kiểm tra terminal Backend có đang chạy không
2. Kiểm tra: `http://localhost:5000/api/health`
3. Nếu không thấy, chạy lại: `python app.py`

### Lỗi: "CORS policy" trong browser console

**Nguyên nhân:** Frontend đang mở bằng `file://` thay vì `http://`

**Giải pháp:**
- **KHÔNG** mở trực tiếp file HTML bằng double-click
- **PHẢI** mở qua web server: `http://localhost:8000/assistant.html`

### Lỗi: Port 5000 đã được sử dụng

**Nguyên nhân:** Có process khác đang dùng port 5000

**Giải pháp:**

**Option 1: Tìm và đóng process**
```powershell
# Tìm process đang dùng port 5000
netstat -ano | findstr :5000

# Đóng process (thay PID bằng số từ lệnh trên)
taskkill /PID <PID> /F
```

**Option 2: Đổi port Backend**

Sửa trong `Backend/RAG_chatbot/app.py`:
```python
app.run(host="0.0.0.0", port=5001)  # Đổi port
```

Và cập nhật `Frontend/js/main.js`:
```javascript
API_URL: 'http://localhost:5001/api/chat'
```

### Lỗi: Port 8000 đã được sử dụng

**Giải pháp:** Đổi port frontend

```powershell
python -m http.server 8001  # Dùng port khác
```

Và mở: `http://localhost:8001/assistant.html`

### Lỗi: "ModuleNotFoundError: No module named 'flask'"

**Nguyên nhân:** Chưa cài đặt dependencies

**Giải pháp:**
```powershell
cd "Backend\RAG_chatbot"
pip install -r requirements.txt
```

---

## 📊 SƠ ĐỒ HOẠT ĐỘNG

```
┌─────────────────┐
│   Browser       │
│  (Frontend)     │
│  Port 8000      │
└────────┬────────┘
         │ HTTP Request
         │ (POST /api/chat)
         ▼
┌─────────────────┐
│  Flask API      │
│  (Backend)      │
│  Port 5000      │
└────────┬────────┘
         │
         ├──► MongoDB (Dữ liệu)
         ├──► BGE-M3 (Embeddings)
         └──► Gemini API (LLM)
```

---

## 🎯 QUY TRÌNH CHẠY NHANH

### Lần đầu setup:
```powershell
# 1. Cài đặt
cd "Backend\RAG_chatbot"
pip install -r requirements.txt

# 2. Chuẩn bị dữ liệu
python scripts\index_mongo.py
python scripts\embed_bge_m3.py
```

### Mỗi lần chạy:
```powershell
# Terminal 1: Backend
cd "Backend\RAG_chatbot"
python app.py

# Terminal 2: Frontend
cd "Frontend"
python -m http.server 8000

# Browser: Mở http://localhost:8000/assistant.html
```

---

## 📝 LƯU Ý QUAN TRỌNG

1. **Luôn chạy Backend trước Frontend**
   - Backend cần thời gian load model (~10-30 giây)
   - Frontend sẽ không hoạt động nếu Backend chưa sẵn sàng

2. **Giữ cả 2 terminal mở**
   - Đóng terminal = Đóng server
   - Cần giữ cả 2 terminal chạy đồng thời

3. **Không mở file HTML trực tiếp**
   - Phải dùng web server (http://localhost:8000)
   - Mở bằng file:// sẽ gặp lỗi CORS

4. **Kiểm tra ports**
   - Backend: Port 5000
   - Frontend: Port 8000
   - Đảm bảo không bị chiếm dụng

---

## 🆘 CẦN HỖ TRỢ?

1. **Kiểm tra Backend:**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET
   ```

2. **Kiểm tra Frontend:**
   - Mở browser console (F12)
   - Xem tab Network để kiểm tra requests

3. **Xem logs:**
   - Backend: Xem output trong terminal
   - Frontend: Xem browser console (F12)

---

**Chúc bạn sử dụng thành công! 🎉**









