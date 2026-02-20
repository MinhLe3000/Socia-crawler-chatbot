# Hạn chế, rủi ro kỹ thuật và đề xuất cải thiện

Tài liệu này tổng hợp các hạn chế, rủi ro kỹ thuật và đề xuất cải thiện cho dự án **Socia-crawler-chatbot** (RAG chatbot + crawl Facebook Group).

---

## 1. Hạn chế và rủi ro kỹ thuật

### 1.1. Cấu hình bị phân tán và không nhất quán

- **Vấn đề:** Tồn tại **hai file config** độc lập:
  - `RAG_chatbot/src/utils/config.py` — dùng cho app chính và retriever.
  - `RAG_chatbot/scripts/config.py` — dùng cho các script index/embed.
- **Hệ quả:**
  - Có thể dùng **tên database khác nhau** (ví dụ `Postandcmt` vs `chatbotNeu`).
  - Cách lấy MongoDB URI khác nhau (hardcode vs từ `.env`).
- **Rủi ro:** Khó debug khi deploy; một nơi index vào DB A, app đọc từ DB B.

### 1.2. Hardcode thông tin nhạy cảm

- **Vấn đề:** Trong `src/utils/config.py` có **MongoDB URI được hardcode** trong source code.
- **Rủi ro:**
  - Lộ thông tin kết nối khi đẩy code lên Git (dù `.env` đã được ignore).
  - Không an toàn khi chia sẻ repo hoặc làm việc nhóm.

### 1.3. Requirements không khớp với code

- **Vấn đề:**
  - `RAG_chatbot/requirements.txt` liệt kê `flask`, `flask-cors`.
  - Ứng dụng thực tế dùng **FastAPI** và **uvicorn**.
  - Thiếu `fastapi`, `uvicorn` trong requirements.
- **Hệ quả:**
  - Người mới clone repo cài theo requirements sẽ thiếu dependency để chạy API.
  - Gây nhầm lẫn về framework (Flask vs FastAPI).

### 1.4. Thiếu bộ test chuẩn

- **Vấn đề:**
  - Không có thư mục `tests/` hay cấu hình pytest (`pytest.ini`).
  - Chỉ có `test_api.py` (gửi request thủ công) và `scripts/test_query.py` (test retrieval).
- **Rủi ro:**
  - Refactor hoặc thay đổi logic dễ gây lỗi mà không phát hiện.
  - Khó đảm bảo chất lượng khi mở rộng tính năng.

### 1.5. Quản lý dependency chưa chuẩn hóa

- **Vấn đề:**
  - Mỗi phần có `requirements.txt` riêng (`Crawl_data/` và `RAG_chatbot/`).
  - Không có `pyproject.toml` hoặc file requirements tổng ở root.
- **Hệ quả:** Khó setup môi trường “all-in-one”; phải biết rõ từng phần cần cài gì.

### 1.6. Trùng lặp logic giữa scripts và src

- **Vấn đề:** Scripts trong `RAG_chatbot/scripts` (index, embed) chủ yếu procedural, ít tái sử dụng code từ `src/`.
- **Rủi ro:** Logic truy vấn Mongo / build document cho Qdrant có thể trùng lặp; sửa một nơi dễ quên cập nhật nơi kia.

---

## 2. Đề xuất cải thiện

### 2.1. Chuẩn hóa cấu hình (ưu tiên cao)

- **Mục tiêu:** Một nguồn config duy nhất, mọi thành phần đọc từ đó.
- **Gợi ý:**
  - Dùng **một module config** (ví dụ `src/utils/config.py`) đọc toàn bộ từ biến môi trường (`.env`).
  - `scripts/config.py` nên **import từ** `src.utils.config` hoặc bỏ hẳn, dùng chung config.
  - Đảm bảo **một database name**, **một collection**, **một Qdrant host/port** được định nghĩa ở một chỗ.

### 2.2. Loại bỏ hardcode secrets (ưu tiên cao)

- **Mục tiêu:** Không lưu URI, API key trong source code.
- **Gợi ý:**
  - Xóa mọi MongoDB URI / API key hardcode; thay bằng biến môi trường.
  - Tạo file **`.env.example`** liệt kê các biến cần thiết (không ghi giá trị thật) để người khác biết cách cấu hình.

### 2.3. Sửa và đồng bộ requirements (ưu tiên cao)

- **Mục tiêu:** `pip install -r requirements.txt` đủ để chạy app và scripts.
- **Gợi ý:**
  - Thêm **`fastapi`**, **`uvicorn`** vào `RAG_chatbot/requirements.txt`.
  - Nếu không dùng Flask thực sự thì **bỏ** `flask`, `flask-cors` để tránh nhầm lẫn.
  - Có thể tách **`requirements-dev.txt`** cho công cụ dev/test (pytest, black, v.v.).

### 2.4. Giảm trùng lặp giữa scripts và src (ưu tiên trung bình)

- **Mục tiêu:** Logic index/embed dùng chung code với retriever và app.
- **Gợi ý:**
  - Cho `index_mongo.py`, `embed_bge_m3.py` **gọi hàm từ** `src` (ví dụ module `src.rag.indexing` hoặc tương tự).
  - Tái sử dụng cùng cách kết nối Mongo, cùng cách build document cho Qdrant.
  - Lợi ích: dễ test, tránh bug do cập nhật không đồng bộ.

### 2.5. Bổ sung test cơ bản (ưu tiên trung bình)

- **Mục tiêu:** Có bộ test tự động, chạy bằng pytest.
- **Gợi ý:**
  - Tạo thư mục **`tests/`** và file test cho:
    - Hàm build query / retriever (không cần gọi Gemini).
    - API `/api/chat` với **mock** retriever và LLM.
  - Thêm **`pytest.ini`** hoặc cấu hình trong `pyproject.toml` nếu dùng.
  - Tận dụng `.gitignore` đã ignore `.pytest_cache`.

### 2.6. Chuẩn hóa quản lý dependency (ưu tiên thấp)

- **Mục tiêu:** Dễ cài đặt và bảo trì dependency.
- **Gợi ý:**
  - Cân nhắc **`pyproject.toml`** cho metadata và dependency (theo chuẩn PEP 518/621).
  - Có thể giữ `requirements.txt` sinh từ `pyproject.toml` hoặc dùng trực tiếp `pip install -e .` cho development.

---

## 3. Tóm tắt ưu tiên

| Ưu tiên   | Nội dung                                      |
|----------|-----------------------------------------------|
| **Cao**  | Chuẩn hóa config; bỏ hardcode secrets; sửa requirements |
| **Trung bình** | Giảm trùng lặp scripts/src; thêm test cơ bản   |
| **Thấp** | Chuẩn hóa dependency (pyproject.toml, v.v.)   |

---

*Tài liệu được tạo dựa trên đánh giá repo Socia-crawler-chatbot.*
