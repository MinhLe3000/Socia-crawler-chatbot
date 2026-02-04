# 🚀 CÁCH CHẠY RAG CHATBOT - HƯỚNG DẪN ĐƠN GIẢN

## ⚡ CÁCH CHẠY NHANH NHẤT

### Bước 1: Mở Terminal/Command Prompt
```bash
cd "D:\NEU\Năm 3\Kỳ 2 năm 3\Thầy huy\RAG_chatbot"
```

### Bước 2: Kiểm tra setup (Khuyến nghị)
```bash
python check_setup.py
```

**Kết quả mong đợi:**
- ✅ Tất cả PASS → Tiếp tục bước 3
- ❌ Có lỗi → Sửa lỗi theo hướng dẫn

### Bước 3: Chuẩn bị dữ liệu (CHỈ CHẠY LẦN ĐẦU HOẶC KHI CÓ DỮ LIỆU MỚI)

#### 3.1. Chuẩn hóa dữ liệu từ MongoDB
```bash
python scripts/index_mongo.py
```
**Kết quả:** `Inserted X documents into 'knowledge_base' collection.`

#### 3.2. Tạo embeddings (mất 5-15 phút)
```bash
python scripts/embed_bge_m3.py
```
**Kết quả:** `Hoan thanh. Da cap nhat embedding cho X documents.`

### Bước 4: Chạy Chatbot
```bash
python chat_cli.py
```

**Cách sử dụng:**
```
RAG + Gemini chatbot tren du lieu Facebook group.
Nhap cau hoi (hoac 'exit' de thoat).

You: thầy Phùng Ngọc Tùng dạy cái gì
[Bot trả lời...]

You: exit
```

---

## 📋 CHI TIẾT TỪNG BƯỚC

### BƯỚC 1: Kiểm tra setup

Chạy lệnh:
```bash
python check_setup.py
```

**Script này kiểm tra:**
1. ✅ Python version (cần >= 3.8)
2. ✅ Dependencies đã cài đặt chưa
3. ✅ File `gemini.env` có API key chưa
4. ✅ Kết nối MongoDB
5. ✅ Dữ liệu trong database

**Nếu thiếu dependencies:**
```bash
pip install -r requirements.txt
```

---

### BƯỚC 2: Chuẩn bị dữ liệu

#### **Script 1: `index_mongo.py`**
```bash
python scripts/index_mongo.py
```

**File này làm gì:**
- Đọc `posts` và `comments` từ database **Postandcmt**
- Chuẩn hóa thành format thống nhất
- Ghi vào collection `knowledge_base` trong database **Chatbot**

**Output mẫu:**
```
Inserted 1234 documents into 'knowledge_base' collection.
```

**Khi nào chạy:**
- Lần đầu setup
- Khi có dữ liệu mới trong MongoDB
- Muốn cập nhật lại knowledge_base

---

#### **Script 2: `embed_bge_m3.py`**
```bash
python scripts/embed_bge_m3.py
```

**File này làm gì:**
- Load model BGE-M3 (tự download lần đầu ~2GB)
- Đọc documents từ `knowledge_base`
- Tạo embeddings (dense + sparse) cho mỗi document
- Lưu embeddings vào MongoDB

**Output mẫu:**
```
Starting embedding generation for 1234 documents using BGE-M3...
  - Dense embeddings: ON
  - Sparse embeddings: ON (hybrid search)
Processed 16/1234 documents
Processed 32/1234 documents
...
Hoan thanh. Da cap nhat embedding cho 1234 documents.
```

**Thời gian:**
- 100 documents: ~1-2 phút
- 1000 documents: ~10-15 phút
- Có GPU: Nhanh hơn nhiều

**Lưu ý:**
- Lần đầu chạy sẽ download model (mất vài phút)
- Cần internet ổn định
- Cần RAM ít nhất 4GB

**Khi nào chạy:**
- Sau khi chạy `index_mongo.py`
- Khi có documents mới chưa có embeddings

---

### BƯỚC 3: Chạy Chatbot

```bash
python chat_cli.py
```

**Lần đầu chạy sẽ:**
1. Load model BGE-M3 vào RAM (~10-30 giây)
2. Load embeddings vào RAM (~1-5 giây)
3. Kết nối MongoDB

**Output:**
```
Loaded 1234 embeddings into RAM for RAG.
  - Dense embeddings: 1234
  - Sparse embeddings: 1234/1234
RAG + Gemini chatbot tren du lieu Facebook group.
Nhap cau hoi (hoac 'exit' de thoat).
```

**Sử dụng:**
```
You: thầy Phùng Ngọc Tùng dạy cái gì

--- Bot (Gemini) ---
[Dựa trên thông tin trong knowledge base, bot sẽ trả lời...]

--- Nguon context ---
[DOC 1] final_score=0.856 (dense=0.712)
  text: [Nội dung document 1]
  link: https://facebook.com/...

[DOC 2] final_score=0.789 (dense=0.654)
  text: [Nội dung document 2]
  link: https://facebook.com/...

You: exit
```

---

## 🔄 CÁC TRƯỜNG HỢP SỬ DỤNG

### Lần đầu setup hoàn toàn mới:
```bash
# 1. Kiểm tra
python check_setup.py

# 2. Cài dependencies (nếu chưa có)
pip install -r requirements.txt

# 3. Chuẩn hóa dữ liệu
python scripts/index_mongo.py

# 4. Tạo embeddings
python scripts/embed_bge_m3.py

# 5. Chạy chatbot
python chat_cli.py
```

### Các lần sau (đã có embeddings):
```bash
# Chỉ cần chạy chatbot
python chat_cli.py
```

### Khi có dữ liệu mới trong MongoDB:
```bash
# 1. Cập nhật knowledge_base
python scripts/index_mongo.py

# 2. Tạo embeddings cho documents mới
python scripts/embed_bge_m3.py

# 3. Chạy chatbot
python chat_cli.py
```

---

## ⚠️ XỬ LÝ LỖI THƯỜNG GẶP

### Lỗi: "GEMINI_API_KEY not found"
**Nguyên nhân:** File `gemini.env` chưa đúng hoặc không tồn tại

**Giải pháp:**
1. Kiểm tra file `gemini.env` có trong thư mục `RAG_chatbot`
2. Format đúng: `GEMINI_API_KEY=your_key_here` (KHÔNG có khoảng trắng xung quanh `=`)
3. Không có dấu ngoặc kép

### Lỗi: "No embeddings found in MongoDB"
**Nguyên nhân:** Chưa chạy `embed_bge_m3.py`

**Giải pháp:**
```bash
# Chạy theo thứ tự
python scripts/index_mongo.py
python scripts/embed_bge_m3.py
```

### Lỗi: "No documents found in collection 'knowledge_base'"
**Nguyên nhân:** Chưa có dữ liệu hoặc chưa chạy `index_mongo.py`

**Giải pháp:**
```bash
python scripts/index_mongo.py
```

### Lỗi: MongoDB connection error
**Nguyên nhân:** URI MongoDB sai hoặc không kết nối được

**Giải pháp:**
- Kiểm tra `MONGO_URI` trong `src/utils/config.py`
- Kiểm tra kết nối internet
- Kiểm tra MongoDB Atlas whitelist IP (nếu dùng cloud)

### Lỗi: "Module not found" hoặc thiếu packages
**Giải pháp:**
```bash
pip install -r requirements.txt
```

---

## 🎯 TÓM TẮT QUY TRÌNH

```
┌─────────────────────────────────────┐
│  1. python check_setup.py          │
│     ↓                               │
│  2. python scripts/index_mongo.py  │
│     ↓                               │
│  3. python scripts/embed_bge_m3.py │
│     ↓                               │
│  4. python chat_cli.py             │
└─────────────────────────────────────┘
```

**Lần đầu:** Chạy cả 4 bước
**Lần sau:** Chỉ chạy bước 4

---

## 💡 LƯU Ý

1. **File `gemini.env`:** Phải có trong thư mục `RAG_chatbot`, format: `KEY=value` (không có khoảng trắng)
2. **Thời gian:** Lần đầu mất nhiều thời gian vì download model (~2GB)
3. **RAM:** Cần ít nhất 4GB RAM để chạy ổn định
4. **GPU:** Không bắt buộc nhưng sẽ nhanh hơn nhiều khi tạo embeddings

---

## 🆘 CẦN HỖ TRỢ?

- Chạy `python check_setup.py` để kiểm tra lỗi
- Xem file `HUONG_DAN_CHAY.md` để biết chi tiết
- Kiểm tra file `README.md` để hiểu kiến trúc





