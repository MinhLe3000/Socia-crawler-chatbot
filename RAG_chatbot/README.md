# 🚀 HƯỚNG DẪN CHẠY RAG CHATBOT - HƯỚNG DẪN CHI TIẾT

## 📋 Mục lục

1. [Tổng quan](#tổng-quan)
2. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
3. [Cài đặt từng bước](#cài-đặt-từng-bước)
4. [Chuẩn bị dữ liệu](#chuẩn-bị-dữ-liệu)
5. [Chạy Chatbot](#chạy-chatbot)
6. [Các trường hợp sử dụng](#các-trường-hợp-sử-dụng)
7. [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp)
8. [Cấu hình nâng cao](#cấu-hình-nâng-cao)
9. [Kiểm tra và Debug](#kiểm-tra-và-debug)

---

## 🎯 Tổng quan

RAG Chatbot là hệ thống chatbot sử dụng kỹ thuật **Retrieval-Augmented Generation (RAG)** để trả lời câu hỏi dựa trên dữ liệu từ Facebook Group. Hệ thống kết hợp:

- **BGE-M3**: Model embedding đa ngôn ngữ để tìm kiếm semantic
- **Hybrid Search**: Kết hợp dense (semantic) và sparse (keyword) embeddings
- **Google Gemini 2.5 Flash**: LLM để sinh câu trả lời tự nhiên
- **MongoDB**: Lưu trữ dữ liệu và embeddings

### Quy trình hoạt động:

```
1. User Query → Encode thành vectors
2. Hybrid Search → Tìm top-K documents liên quan
3. Build Context → Format post + comments
4. Gemini LLM → Sinh câu trả lời từ context
5. Display Answer + Source Links
```

---

## 💻 Yêu cầu hệ thống

### Phần mềm cần thiết:

- **Python 3.8+** (khuyến nghị 3.9 hoặc 3.10)
- **pip** (package manager)
- **Git** (nếu clone từ repository)

### Tài nguyên phần cứng:

- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB+)
- **Ổ cứng**: ~5GB trống (cho model và dependencies)
- **GPU**: Không bắt buộc nhưng sẽ tăng tốc đáng kể khi tạo embeddings
- **Internet**: Cần để download model và kết nối API

### Tài khoản và API Keys:

1. **Google Gemini API Key**
   - Truy cập: https://aistudio.google.com/app/apikey
   - Tạo API key mới
   - Lưu lại để cấu hình

2. **MongoDB Database**
   - Đã có MongoDB với dữ liệu `posts` và `comments`
   - Hoặc sử dụng MongoDB Atlas (cloud)
   - Connection string đã được cấu hình trong `src/utils/config.py`

---

## 📦 Cài đặt từng bước

### Bước 1: Kiểm tra Python

```bash
# Kiểm tra Python version
python --version
# hoặc
py --version
# hoặc
python3 --version
```

**Yêu cầu**: Python >= 3.8

Nếu chưa có Python, tải từ: https://www.python.org/downloads/

### Bước 2: Di chuyển vào thư mục dự án

```bash
# Windows PowerShell
cd "D:\NEU\Năm 3\Kỳ 2 năm 3\Thầy huy\RAG_chatbot"

# Windows Command Prompt
cd /d "D:\NEU\Năm 3\Kỳ 2 năm 3\Thầy huy\RAG_chatbot"

# Linux/Mac
cd "/path/to/RAG_chatbot"
```

**Lưu ý**: Luôn chạy các lệnh từ thư mục `RAG_chatbot` này.

### Bước 3: Tạo Virtual Environment (Khuyến nghị)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

Sau khi activate, prompt sẽ hiển thị `(venv)` ở đầu dòng.

### Bước 4: Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

**Lưu ý**: 
- Lần đầu cài đặt có thể mất 5-15 phút
- Cần tải PyTorch (~1-2GB) và các thư viện lớn khác
- Đảm bảo kết nối internet ổn định

**Nếu gặp lỗi protobuf**, xem [Xử lý lỗi protobuf](#lỗi-protobuf).

### Bước 5: Cấu hình Gemini API Key

Tạo file `gemini.env` trong thư mục `RAG_chatbot`:

```bash
# Windows PowerShell
echo "GEMINI_API_KEY=your_api_key_here" > gemini.env

# Linux/Mac
echo "GEMINI_API_KEY=your_api_key_here" > gemini.env
```

Hoặc tạo file thủ công:

1. Tạo file mới tên `gemini.env` trong thư mục `RAG_chatbot`
2. Thêm nội dung:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```
3. Lưu file

**⚠️ QUAN TRỌNG**: 
- Không có khoảng trắng xung quanh dấu `=`
- Không có dấu ngoặc kép
- Thay `your_actual_api_key_here` bằng API key thật của bạn

### Bước 6: Kiểm tra MongoDB Configuration

Kiểm tra file `src/utils/config.py`:

```python
MONGO_URI = "mongodb+srv://..."  # Connection string của bạn
MONGO_DB_SOURCE = "Postandcmt"   # Database chứa posts/comments
MONGO_DB_NAME = "Chatbot"         # Database chứa knowledge_base
```

Nếu cần thay đổi, sửa các giá trị này.

### Bước 7: Kiểm tra Setup

```bash
python check_setup.py
```

Script này sẽ kiểm tra:
- ✅ Python version
- ✅ Dependencies đã cài đặt
- ✅ Gemini API key
- ✅ MongoDB connection
- ✅ Dữ liệu trong database
- ✅ Knowledge base và embeddings

**Kết quả mong đợi**: Tất cả đều PASS (✅)

Nếu có lỗi, xem phần [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp).

---

## 🗂️ Chuẩn bị dữ liệu

**⚠️ LƯU Ý**: Các bước này chỉ cần chạy **LẦN ĐẦU** hoặc khi có **DỮ LIỆU MỚI**.

### Bước 1: Chuẩn hóa dữ liệu từ MongoDB

```bash
python scripts/index_mongo.py
```

**File này làm gì:**
- Đọc tất cả `posts` và `comments` từ database `Postandcmt`
- Chuẩn hóa thành format thống nhất
- Lưu vào collection `knowledge_base` trong database `Chatbot`
- **Xóa và rebuild** toàn bộ knowledge_base (nếu đã có)

**Output mẫu:**
```
Inserted 1234 documents into 'knowledge_base' collection.
```

**Kết quả**: Collection `knowledge_base` được tạo với format:
```json
{
  "_id": "post::123" hoặc "comment::456",
  "type": "post" hoặc "comment",
  "text": "Nội dung bài đăng/bình luận",
  "source": {
    "post_id": "...",
    "permalink_url": "https://facebook.com/..."
  },
  "created_time": "...",
  "fetched_at": "..."
}
```

**Thời gian**: ~1-5 giây (tùy số lượng documents)

### Bước 2: Tạo Embeddings

```bash
python scripts/embed_bge_m3.py
```

**File này làm gì:**
- Load model BGE-M3 (lần đầu sẽ tự động download ~2GB)
- Đọc tất cả documents từ `knowledge_base`
- Tạo **dense embeddings** (1024 chiều) cho mỗi document
- Tạo **sparse embeddings** (keyword-based) cho hybrid search
- Lưu embeddings vào MongoDB cùng với document gốc
- Xử lý theo batch (mặc định 16 documents/batch)

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

**Kết quả**: Mỗi document trong `knowledge_base` sẽ có thêm:
```json
{
  "embedding": [0.123, -0.456, ...],  // Vector 1024 chiều (float32)
  "sparse_embedding": {123: 0.5, 456: 0.3, ...},  // Dict token_id: weight
  "embedding_dim": 1024,
  "embedding_model": "BAAI/bge-m3"
}
```

**Thời gian** (ước tính):
- 100 documents: ~1-2 phút
- 500 documents: ~5-8 phút
- 1000 documents: ~10-15 phút
- 5000+ documents: ~30-60 phút
- **Có GPU**: Nhanh hơn 5-10 lần

**Lưu ý**:
- Lần đầu chạy sẽ download model BGE-M3 (~2GB) → mất vài phút
- Cần internet ổn định để download model
- Cần RAM ít nhất 4GB
- Có thể tăng `batch_size` trong script nếu có nhiều RAM/GPU

**Khi nào chạy lại:**
- Sau khi chạy `index_mongo.py` (có documents mới)
- Khi có documents trong knowledge_base chưa có embeddings

---

## 💬 Chạy Chatbot

### Chạy Chatbot chính

```bash
python chat_cli.py
```

### Quá trình khởi động:

1. **Load API Key**: Đọc từ `gemini.env`
2. **Kết nối MongoDB**: Kết nối đến database
3. **Load Model BGE-M3**: Load model vào RAM (~10-30 giây lần đầu)
4. **Load Embeddings Cache**: Load tất cả embeddings vào RAM (~1-5 giây)
5. **Load Comments Cache**: Map post_id → comments
6. **Sẵn sàng**: Hiển thị prompt để nhập câu hỏi

**Output khi khởi động:**
```
Loaded 1234 embeddings into RAM for RAG.
  - Dense embeddings: 1234
  - Sparse embeddings: 1234/1234
Loaded 567 comments for 123 posts.
✅ Đang sử dụng model: gemini-2.5-flash
RAG + Gemini chatbot tren du lieu Facebook group.
Nhap cau hoi (hoac 'exit' de thoat).
```

### Cách sử dụng:

```
You: thầy Phùng Ngọc Tùng dạy cái gì

--- Bot (Gemini) ---
[Dựa trên thông tin trong knowledge base, bot sẽ trả lời câu hỏi...]

--- Bài viết đã dùng để trả lời ---
1. https://www.facebook.com/groups/.../permalink/...

--- Các bài viết liên quan ---
2. https://www.facebook.com/groups/.../permalink/...
3. https://www.facebook.com/groups/.../permalink/...
```

### Quy trình xử lý một câu hỏi:

1. **Encode Query**: Chuyển câu hỏi thành dense + sparse vectors
2. **Hybrid Search**: 
   - Tính dense similarity (cosine similarity)
   - Tính sparse similarity (BM25-like token matching)
   - Kết hợp: `final_score = 0.7 * dense + 0.3 * sparse`
3. **Top-K Selection**: Chọn top 5 documents có điểm cao nhất
4. **Build Context**: Format post + comments thành context string
5. **Generate Prompt**: Tạo prompt cho Gemini với context + question
6. **Call Gemini API**: Gửi prompt và nhận câu trả lời
7. **Display**: Hiển thị câu trả lời + source links

### Thoát chatbot:

```
You: exit
```
hoặc
```
You: quit
```

### Test Retrieval (Không cần Gemini API)

```bash
python scripts/test_query.py
```

**File này làm gì:**
- Test riêng phần RAG retrieval (không gọi Gemini)
- Hiển thị documents được tìm thấy và scores
- Hữu ích để debug hoặc kiểm tra chất lượng retrieval

**Output mẫu:**
```
Loading RAG retriever...
TEST QUERY: thầy Phùng Ngọc Tùng dạy cái gì

Found 5 results:

[DOC 1]
  Final Score: 0.856
  Dense Score: 0.712
  Text: [200 ký tự đầu của document]...
  Link: https://www.facebook.com/...

[DOC 2]
  Final Score: 0.789
  Dense Score: 0.654
  Text: ...
  Link: ...
```

---

## 🔄 Các trường hợp sử dụng

### Trường hợp 1: Setup lần đầu (hoàn toàn mới)

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Tạo file gemini.env với API key

# 3. Kiểm tra setup
python check_setup.py

# 4. Chuẩn hóa dữ liệu
python scripts/index_mongo.py

# 5. Tạo embeddings (mất thời gian nhất)
python scripts/embed_bge_m3.py

# 6. Chạy chatbot
python chat_cli.py
```

### Trường hợp 2: Đã có embeddings (chạy lại)

```bash
# Chỉ cần chạy chatbot
python chat_cli.py
```

**Lưu ý**: 
- Embeddings được cache trong RAM khi khởi động
- Không cần chạy lại `index_mongo.py` và `embed_bge_m3.py`
- Chỉ cần chạy khi có dữ liệu mới

### Trường hợp 3: Có dữ liệu mới trong MongoDB

```bash
# 1. Cập nhật knowledge_base (xóa và rebuild)
python scripts/index_mongo.py

# 2. Tạo embeddings cho documents mới
python scripts/embed_bge_m3.py

# 3. Chạy chatbot
python chat_cli.py
```

**Lưu ý**: 
- `index_mongo.py` sẽ **xóa toàn bộ** knowledge_base và rebuild
- `embed_bge_m3.py` sẽ tạo embeddings cho **tất cả** documents (kể cả cũ)
- Nếu có nhiều documents, có thể mất thời gian

### Trường hợp 4: Chỉ test retrieval (không cần Gemini)

```bash
python scripts/test_query.py
```

Hữu ích khi:
- Chưa có Gemini API key
- Muốn kiểm tra chất lượng retrieval
- Debug vấn đề tìm kiếm

---

## 🐛 Xử lý lỗi thường gặp

### Lỗi 1: "GEMINI_API_KEY not found"

**Nguyên nhân**: File `gemini.env` không tồn tại hoặc format sai

**Giải pháp**:

1. **Kiểm tra file có tồn tại:**
   ```bash
   # Windows PowerShell
   Test-Path gemini.env
   
   # Linux/Mac
   ls gemini.env
   ```

2. **Kiểm tra format file:**
   ```bash
   # Windows PowerShell
   Get-Content gemini.env
   
   # Linux/Mac
   cat gemini.env
   ```
   
   Phải hiển thị: `GEMINI_API_KEY=your_key_here` (KHÔNG có khoảng trắng)

3. **Sửa file nếu sai:**
   - Mở file `gemini.env` bằng text editor
   - Đảm bảo format: `GEMINI_API_KEY=your_key_here`
   - Không có khoảng trắng xung quanh dấu `=`
   - Không có dấu ngoặc kép
   - Lưu file

### Lỗi 2: "No embeddings found in MongoDB"

**Nguyên nhân**: Chưa chạy `embed_bge_m3.py` hoặc chưa có knowledge_base

**Giải pháp**:

```bash
# Chạy theo thứ tự
python scripts/index_mongo.py
python scripts/embed_bge_m3.py
```

**Kiểm tra sau khi chạy:**
```python
from src.utils.config import get_mongo_client, MONGO_DB_NAME

client = get_mongo_client()
db = client[MONGO_DB_NAME]
kb_count = db.knowledge_base.count_documents({"embedding": {"$exists": True}})
print(f"Documents with embeddings: {kb_count}")
```

### Lỗi 3: "No documents found in collection 'knowledge_base'"

**Nguyên nhân**: Chưa có dữ liệu trong MongoDB hoặc chưa chạy `index_mongo.py`

**Giải pháp**:

1. **Kiểm tra MongoDB có dữ liệu:**
   ```python
   from src.utils.config import get_mongo_client, MONGO_DB_SOURCE
   
   client = get_mongo_client()
   source_db = client[MONGO_DB_SOURCE]
   posts_count = source_db.posts.count_documents({})
   comments_count = source_db.comments.count_documents({})
   print(f"Posts: {posts_count}, Comments: {comments_count}")
   ```

2. **Nếu có dữ liệu, chạy index:**
   ```bash
   python scripts/index_mongo.py
   ```

### Lỗi 4: MongoDB Connection Error

**Lỗi mẫu:**
```
pymongo.errors.ServerSelectionTimeoutError
pymongo.errors.ConfigurationError
```

**Giải pháp**:

1. **Kiểm tra MongoDB URI:**
   ```python
   # Xem file config
   # src/utils/config.py
   ```

2. **Kiểm tra kết nối internet**

3. **Kiểm tra MongoDB Atlas (nếu dùng cloud):**
   - IP address đã được whitelist chưa?
   - Connection string đúng chưa?
   - Database và collections có tồn tại không?

4. **Test kết nối:**
   ```python
   from src.utils.config import get_mongo_client
   
   try:
       client = get_mongo_client()
       client.admin.command('ping')
       print("✅ MongoDB connection OK")
   except Exception as e:
       print(f"❌ MongoDB connection failed: {e}")
   ```

### Lỗi 5: "ModuleNotFoundError: No module named 'X'"

**Nguyên nhân**: Thiếu dependencies

**Giải pháp**:

```bash
# Cài lại dependencies
pip install -r requirements.txt

# Hoặc cài từng package
pip install pymongo python-dotenv torch transformers FlagEmbedding google-generativeai numpy
```

**Nếu vẫn lỗi:**
```bash
# Upgrade pip trước
pip install --upgrade pip

# Cài lại
pip install -r requirements.txt
```

### Lỗi 6: Out of Memory khi tạo embeddings

**Nguyên nhân**: Batch size quá lớn hoặc RAM không đủ

**Giải pháp**:

1. **Giảm batch size:**
   - Mở file `scripts/embed_bge_m3.py`
   - Tìm dòng: `embed_knowledge_base(batch_size=16)`
   - Giảm xuống: `batch_size=8` hoặc `batch_size=4`

2. **Đóng các ứng dụng khác** để giải phóng RAM

3. **Chạy lại:**
   ```bash
   python scripts/embed_bge_m3.py
   ```

### Lỗi 7: Model BGE-M3 tải chậm

**Nguyên nhân**: Lần đầu sử dụng cần download model (~2GB)

**Giải pháp**:

- Đảm bảo kết nối internet ổn định
- Model sẽ được cache, lần sau sẽ nhanh hơn
- Thời gian download: ~5-10 phút tùy tốc độ mạng

### Lỗi 8: Protobuf compatibility

**Lỗi mẫu:**
```
cannot import name 'runtime_version' from 'google.protobuf'
```

**Giải pháp**:

```bash
# Upgrade protobuf
pip install --upgrade protobuf

# Hoặc cài version cụ thể
pip install "protobuf>=4.21.0,<6.0.0"
```

Xem chi tiết trong file `SUA_LOI_PROTOBUF.md`.

### Lỗi 9: PowerShell execution policy

**Lỗi mẫu:**
```
cannot be loaded because running scripts is disabled on this system
```

**Giải pháp**:

Mở PowerShell với quyền Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Xem chi tiết trong file `XU_LY_LOI_POWERSHELL.md`.

### Lỗi 10: "ModuleNotFoundError: No module named 'src'"

**Nguyên nhân**: Chạy từ thư mục sai

**Giải pháp**:

```bash
# Phải chạy từ thư mục RAG_chatbot
cd "D:\NEU\Năm 3\Kỳ 2 năm 3\Thầy huy\RAG_chatbot"

# Kiểm tra bạn đang ở đúng thư mục
pwd  # Linux/Mac
Get-Location  # Windows PowerShell

# Sau đó mới chạy
python chat_cli.py
```

---

## ⚙️ Cấu hình nâng cao

### Thay đổi số lượng documents trả về

Trong file `chat_cli.py`, dòng 59:

```python
docs = retriever.retrieve(question, top_k=5)  # Thay 5 thành số bạn muốn
```

**Khuyến nghị**: 3-10 documents (5 là tốt nhất cho cân bằng giữa chất lượng và tốc độ)

### Thay đổi trọng số Hybrid Search

Trong file `chat_cli.py`, dòng 42:

```python
retriever = RAGRetriever(
    use_hybrid=True,
    dense_weight=0.7,  # Tăng nếu muốn semantic nhiều hơn (0.0-1.0)
    sparse_weight=0.3  # Tăng nếu muốn keyword nhiều hơn (0.0-1.0)
)
```

**Giải thích**:
- `dense_weight` cao → Tìm kiếm theo nghĩa (semantic) nhiều hơn
- `sparse_weight` cao → Tìm kiếm theo từ khóa (keyword) nhiều hơn
- Tổng phải = 1.0 (hoặc hệ thống sẽ tự normalize)

### Thay đổi batch size khi tạo embeddings

Trong file `scripts/embed_bge_m3.py`, dòng 89:

```python
embed_knowledge_base(
    batch_size=16,  # Tăng nếu có nhiều RAM/GPU (ví dụ: 32, 64)
    use_sparse=True  # Tắt nếu không muốn hybrid search
)
```

**Khuyến nghị**:
- RAM 4GB: `batch_size=8`
- RAM 8GB: `batch_size=16`
- RAM 16GB+: `batch_size=32` hoặc `64`
- Có GPU: `batch_size=64` hoặc `128`

### Tắt Hybrid Search (chỉ dùng Dense)

Trong file `chat_cli.py`:

```python
retriever = RAGRetriever(use_hybrid=False)
```

**Khi nào dùng**:
- Khi muốn tốc độ nhanh hơn (không cần tính sparse similarity)
- Khi sparse embeddings không có sẵn
- Khi chỉ quan tâm semantic search

### Thay đổi score threshold

Trong file `chat_cli.py`, dòng 49:

```python
MIN_SCORE_THRESHOLD = 0.3  # Tăng nếu muốn kết quả chính xác hơn (0.0-1.0)
```

**Giải thích**:
- `0.3`: Chấp nhận kết quả có độ tương đồng thấp
- `0.5`: Chỉ chấp nhận kết quả có độ tương đồng trung bình
- `0.7`: Chỉ chấp nhận kết quả có độ tương đồng cao

### Thay đổi Gemini Model

Trong file `chat_cli.py`, hàm `get_gemini_model()`:

```python
model = genai.GenerativeModel("gemini-2.5-flash")  # Model hiện tại
# Có thể thay bằng:
# model = genai.GenerativeModel("gemini-pro")
# model = genai.GenerativeModel("gemini-1.5-pro")
```

**Lưu ý**: Kiểm tra model nào có sẵn trong Gemini API của bạn.

---

## 🔍 Kiểm tra và Debug

### Kiểm tra MongoDB có dữ liệu

```python
from src.utils.config import get_mongo_client, MONGO_DB_SOURCE, MONGO_DB_NAME

client = get_mongo_client()

# Kiểm tra source database
source_db = client[MONGO_DB_SOURCE]
posts_count = source_db.posts.count_documents({})
comments_count = source_db.comments.count_documents({})
print(f"Source DB '{MONGO_DB_SOURCE}':")
print(f"  - Posts: {posts_count}")
print(f"  - Comments: {comments_count}")

# Kiểm tra target database
target_db = client[MONGO_DB_NAME]
kb_count = target_db.knowledge_base.count_documents({})
with_emb = target_db.knowledge_base.count_documents({"embedding": {"$exists": True}})
print(f"\nTarget DB '{MONGO_DB_NAME}':")
print(f"  - Knowledge Base: {kb_count}")
print(f"  - With embeddings: {with_emb}/{kb_count}")
```

### Kiểm tra embeddings đã được tạo

```python
from src.utils.config import get_mongo_client, MONGO_DB_NAME

client = get_mongo_client()
db = client[MONGO_DB_NAME]

# Lấy một document mẫu
sample = db.knowledge_base.find_one({"embedding": {"$exists": True}})
if sample:
    print(f"✅ Embeddings OK")
    print(f"  - Embedding dimension: {sample.get('embedding_dim')}")
    print(f"  - Has sparse: {bool(sample.get('sparse_embedding'))}")
    print(f"  - Model: {sample.get('embedding_model')}")
else:
    print("❌ No embeddings found")
```

### Test RAG Retrieval

```bash
python scripts/test_query.py
```

Hoặc tự viết script test:

```python
from src.rag import RAGRetriever

retriever = RAGRetriever(use_hybrid=True)
docs = retriever.retrieve("thầy Phùng Ngọc Tùng dạy cái gì", top_k=5)

for i, doc in enumerate(docs, 1):
    print(f"[DOC {i}] Score: {doc['score']:.3f}")
    print(f"  Text: {doc['text'][:100]}...")
    print(f"  Link: {doc['source'].get('permalink_url', 'N/A')}")
    print()
```

### Kiểm tra Gemini API Key

```python
import os
from dotenv import load_dotenv

load_dotenv("gemini.env")
api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    print(f"✅ API Key found: {api_key[:10]}...")
else:
    print("❌ API Key not found")
```

### Debug với verbose output

Thêm vào đầu file `chat_cli.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📊 Tóm tắt quy trình chạy

### Lần đầu setup:

```
1. pip install -r requirements.txt
2. Tạo gemini.env với API key
3. python check_setup.py
4. python scripts/index_mongo.py
5. python scripts/embed_bge_m3.py
6. python chat_cli.py
```

### Các lần sau:

```
python chat_cli.py
```

### Khi có dữ liệu mới:

```
1. python scripts/index_mongo.py
2. python scripts/embed_bge_m3.py
3. python chat_cli.py
```

---

## 💡 Lưu ý quan trọng

1. **File `gemini.env`**: 
   - Phải có trong thư mục `RAG_chatbot`
   - Format: `GEMINI_API_KEY=your_key` (không có khoảng trắng)
   - Không được commit vào git

2. **Model BGE-M3**: 
   - Tự động download lần đầu (~2GB)
   - Được cache, lần sau nhanh hơn
   - Cần internet để download

3. **Embeddings**: 
   - Được cache trong RAM khi chạy chatbot
   - Khởi động sẽ mất vài giây để load
   - Cần RAM đủ để cache

4. **MongoDB**: 
   - Phải có dữ liệu trong `posts` và `comments` trước
   - Connection string trong `src/utils/config.py`
   - Kiểm tra IP whitelist nếu dùng Atlas

5. **GPU**: 
   - Không bắt buộc
   - Sẽ tăng tốc embedding generation đáng kể
   - Không ảnh hưởng đến retrieval (đã cache trong RAM)

6. **Memory**: 
   - Tối thiểu 4GB RAM cho dataset nhỏ
   - Khuyến nghị 8GB+ cho dataset lớn
   - Embeddings được cache trong RAM

---

## 🆘 Cần hỗ trợ?

1. **Chạy check setup:**
   ```bash
   python check_setup.py
   ```

2. **Xem các file hướng dẫn khác:**
   - `QUICK_START.md`: Hướng dẫn nhanh
   - `HUONG_DAN_CHAY.md`: Hướng dẫn chi tiết tiếng Việt
   - `CACH_CHAY.md`: Cách chạy đơn giản
   - `SUA_LOI_PROTOBUF.md`: Sửa lỗi protobuf
   - `XU_LY_LOI_POWERSHELL.md`: Xử lý lỗi PowerShell

3. **Kiểm tra logs**: Đọc kỹ thông báo lỗi để biết chính xác vấn đề

4. **Test từng bước**: Chạy từng script riêng để xác định lỗi ở đâu

---

**Chúc bạn sử dụng thành công! 🎉**
