# 🚀 HƯỚNG DẪN CHẠY FLASK API CHO RAG CHATBOT

## 📋 Tổng quan

Flask API server cung cấp REST API endpoints để frontend có thể tương tác với RAG Chatbot.

## ⚙️ Cài đặt

### Bước 1: Cài đặt dependencies

```bash
cd "Backend/RAG_chatbot"
pip install -r requirements.txt
```

**Lưu ý**: File `requirements.txt` đã được cập nhật với Flask và flask-cors.

### Bước 2: Kiểm tra setup

```bash
python check_setup.py
```

Đảm bảo tất cả đều PASS (✅).

### Bước 3: Chuẩn bị dữ liệu (nếu chưa có)

```bash
# Chỉ cần chạy lần đầu hoặc khi có dữ liệu mới
python scripts/index_mongo.py
python scripts/embed_bge_m3.py
```

## 🚀 Chạy API Server

### Chạy server

```bash
python app.py
```

Server sẽ chạy tại: `http://localhost:5000`

**Output mẫu:**
```
Starting RAG Chatbot API server...
Loading RAG retriever and Gemini model...
Loaded 1234 embeddings into RAM for RAG.
  - Dense embeddings: 1234
  - Sparse embeddings: 1234/1234
Loaded 567 comments for 123 posts.
✅ RAG retriever and Gemini model loaded successfully!
 * Running on http://0.0.0.0:5000
```

## 📡 API Endpoints

### 1. Health Check

**GET** `/api/health`

Kiểm tra server có đang chạy không.

**Response:**
```json
{
  "status": "ok",
  "message": "RAG Chatbot API is running"
}
```

### 2. Chat

**POST** `/api/chat`

Gửi câu hỏi và nhận câu trả lời từ RAG chatbot.

**Request Body:**
```json
{
  "question": "thầy Phùng Ngọc Tùng dạy cái gì"
}
```

**Response (Success):**
```json
{
  "success": true,
  "answer": "Thầy Phùng Ngọc Tùng dạy môn...",
  "sources": [
    {
      "link": "https://www.facebook.com/groups/.../permalink/...",
      "text": "Nội dung bài viết..."
    }
  ]
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Error message here"
}
```

## 🔧 Cấu hình Frontend

Frontend đã được cập nhật để gọi API tại `http://localhost:5000/api/chat`.

Nếu muốn thay đổi URL API, sửa trong file `Frontend/js/main.js`:

```javascript
const aiAssistant = {
    API_URL: 'http://localhost:5000/api/chat',  // Thay đổi URL ở đây
    // ...
};
```

## 🧪 Test API

### Sử dụng curl

```bash
# Health check
curl http://localhost:5000/api/health

# Chat
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "thầy Phùng Ngọc Tùng dạy cái gì"}'
```

### Sử dụng Python

```python
import requests

# Health check
response = requests.get('http://localhost:5000/api/health')
print(response.json())

# Chat
response = requests.post(
    'http://localhost:5000/api/chat',
    json={'question': 'thầy Phùng Ngọc Tùng dạy cái gì'}
)
print(response.json())
```

## ⚠️ Lưu ý

1. **CORS**: API đã được cấu hình CORS để frontend có thể gọi được.

2. **Port**: Mặc định chạy trên port 5000. Nếu port này đã được sử dụng, có thể thay đổi trong `app.py`:
   ```python
   app.run(host="0.0.0.0", port=5001)  # Thay đổi port
   ```

3. **Performance**: 
   - Lần đầu chạy sẽ mất thời gian để load model BGE-M3 và embeddings (~10-30 giây)
   - Sau đó, embeddings được cache trong RAM nên sẽ nhanh hơn

4. **Memory**: Cần đủ RAM để cache embeddings. Khuyến nghị ít nhất 4GB.

## 🐛 Xử lý lỗi

### Lỗi "Connection refused"

- Kiểm tra API server đã chạy chưa: `python app.py`
- Kiểm tra port có đúng không (mặc định 5000)

### Lỗi "GEMINI_API_KEY not found"

- Kiểm tra file `gemini.env` có tồn tại không
- Kiểm tra format: `GEMINI_API_KEY=your_key_here` (không có khoảng trắng)

### Lỗi "No embeddings found"

- Chạy: `python scripts/embed_bge_m3.py`

### Lỗi CORS

- API đã được cấu hình CORS, nhưng nếu vẫn lỗi, kiểm tra:
  - Frontend và API có cùng origin không
  - Browser có chặn CORS không

## 📝 Quy trình chạy đầy đủ

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Kiểm tra setup
python check_setup.py

# 3. Chuẩn bị dữ liệu (nếu chưa có)
python scripts/index_mongo.py
python scripts/embed_bge_m3.py

# 4. Chạy API server
python app.py

# 5. Mở frontend trong browser
# Truy cập: http://localhost/assistant.html (hoặc đường dẫn tương ứng)
```

## 🎉 Hoàn thành!

Bây giờ bạn có thể:
1. Chạy API server: `python app.py`
2. Mở trang `assistant.html` trong browser
3. Gửi câu hỏi và nhận câu trả lời từ RAG chatbot!









