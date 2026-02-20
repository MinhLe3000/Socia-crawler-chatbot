# Code Review — Socia-crawler-chatbot

Tài liệu đánh giá chất lượng code, kiến trúc và khả năng vận hành của dự án **Socia-crawler-chatbot** (RAG chatbot + crawl Facebook Group).

---

## 1. Vấn đề nghiêm trọng

### 1.1. Thiếu preprocessing & cleaning data
- Code của bạn chỉ `.strip()` message và thay bằng `[NO_MESSAGE]` nếu rỗng
- **Thực tế**: Posts/comments trên Facebook rất nhiễu:
  - Emoji spam (🔥🔥🔥, ❤️❤️❤️)
  - Link rác, mã giới thiệu
  - Chữ viết tắt teen code ("ông nội", "mik", "vs", "dc")
  - Duplicate content (copy-paste)
  - Comments 1-2 từ vô nghĩa ("oke", "đã xem", ".")

**Hậu quả:** RAG retrieval sẽ trả về nhiều kết quả vô nghĩa, LLM sẽ bị nhiễu.

**Giải pháp cần có:**
```python
# Ví dụ pipeline cleaning cơ bản
def clean_text(text: str) -> str:
    # Remove excessive emojis (keep max 2)
    # Normalize teen code → formal Vietnamese
    # Remove URLs/phone numbers
    # Filter out messages < 10 words
    # Deduplicate near-identical texts
    pass
```

---

### 1.2. Không có document ranking/filtering thông minh
- Bạn chỉ lấy top-5 docs dựa trên similarity score
- **Thực tế**: Trong group sinh viên, 1 topic nóng có thể có 500 comments tương tự nhau ("mình cũng vậy", "đúng rồi")

**Hậu quả:** Top-5 kết quả đều là comments chung chung, thiếu thông tin đa dạng.

**Giải pháp:**
- MMR (Maximal Marginal Relevance) để đảm bảo diversity
- Prioritize posts > comments (posts thường có info density cao hơn)
- Clustering để nhóm các comments tương tự, chỉ lấy representative

---

### 1.3. Prompt engineering cần tiếp tục cải thiện

**Trạng thái hiện tại:** Prompt đã được cải thiện so với phiên bản ban đầu. Hiện tại `build_prompt()` trong `retriever.py` đã có:
- Yêu cầu chỉ dùng thông tin trong context
- Xử lý quan điểm trái chiều
- Yêu cầu trả lời ngắn gọn, tối ưu token
- Thông báo khi không có dữ liệu

**Vẫn còn thiếu:**
- Không có persona/tone guidance (sinh viên thích câu trả lời thân thiện, dễ hiểu)
- Không yêu cầu cite sources dạng `[DOC X]` trong câu trả lời
- Prompt viết không dấu tiếng Việt, có thể ảnh hưởng đến chất lượng output của LLM

**Prompt đề xuất bổ sung:**
```python
"""Bạn là trợ lý AI của nhóm sinh viên, giúp tóm tắt thông tin từ các bài đăng và bình luận.

NHIỆM VỤ:
1. Đọc kỹ các documents được cung cấp
2. Tổng hợp thông tin theo thứ tự ưu tiên: bài viết gốc → comments có nội dung cụ thể
3. Nếu có ý kiến trái chiều, trình bày cả hai phía
4. Trả lời ngắn gọn, dễ hiểu, thân thiện (2-3 đoạn văn)
5. LUÔN trích dẫn nguồn: "[Bài viết] cho biết..." hoặc "[Comment] đề cập..."

Nếu không tìm thấy thông tin: "Mình không thấy thông tin về vấn đề này trong nhóm. Bạn có thể hỏi cụ thể hơn không?"
"""
```

---

### 1.4. Thiếu evaluation metrics
- Bạn không có cách nào đo lường chất lượng retrieval/generation
- Làm sao biết hybrid search (0.7 dense + 0.3 sparse) là optimal?

**Cần có:**
- Test set với 20-30 câu hỏi mẫu của sinh viên
- Metrics: Recall@K, MRR, nDCG cho retrieval
- Human evaluation cho answer quality (1-5 scale)

---

### 1.5. Không handle temporal information
```python
"source": {
    "post_id": post_id,
    "permalink_url": post.get("permalink_url"),
},
"created_time": post.get("created_time"),  # ← Chưa dùng trong retrieval
```

**Vấn đề**: Thông tin về lịch thi, sự kiện, deadline... cần ưu tiên bài post gần đây.

Nên có **recency boosting**: posts trong 7 ngày qua được cộng thêm điểm.

---

### 1.6. Performance concerns

> *Lưu ý: Dự án đã áp dụng Qdrant làm vector database, tuy nhiên vẫn load toàn bộ embeddings vào RAM.*
```python
self.embeddings = np.stack(emb_list, axis=0)  # Load ALL vào RAM
```

**Vấn đề**: 
- Giả sử 10,000 documents × 1024 dims × 4 bytes = ~40MB (OK)
- Nhưng nếu scale lên 100K docs = 400MB
- Nếu có nhiều concurrent users, mỗi request đều tính toán cosine similarity trên toàn bộ corpus

**Giải pháp:** 
- Tận dụng Qdrant search API trực tiếp thay vì load hết vào RAM rồi tính toán bằng numpy
- Hoặc dùng FAISS/Annoy cho approximate nearest neighbor (nhanh hơn 10-100x)
- Hoặc dùng MongoDB Atlas Vector Search (đã support native vector search)

---

### 1.7. Hardcode thông tin nhạy cảm (bảo mật)

- **Vấn đề:** Trong `src/utils/config.py`, MongoDB URI (bao gồm username và password) được **hardcode trực tiếp** trong source code:
  ```python
  MONGO_URI = "mongodb+srv://user:password@cluster..."
  ```
- **Rủi ro:**
  - Lộ thông tin kết nối ngay cả khi `.env` đã được gitignore
  - Bất kỳ ai có quyền truy cập repo đều thấy được credentials
  - Vi phạm nguyên tắc bảo mật cơ bản (secret management)
- **Giải pháp:** Chuyển sang đọc từ biến môi trường: `MONGO_URI = os.getenv("MONGO_URI")`

### 1.8. Cấu hình bị phân tán, tên database không nhất quán

- **Vấn đề:** Tồn tại hai file config riêng biệt:
  - `src/utils/config.py`: database source = `"Postandcmt"`, lấy MONGO_URI bằng hardcode
  - `scripts/config.py`: database source = `"chatbotNeu"`, lấy MONGO_URI từ `.env`
- **Hệ quả:** Scripts index dữ liệu vào database A, nhưng app đọc từ database B — dẫn đến retrieval trả về kết quả rỗng hoặc sai.
- **Giải pháp:** Gộp thành một file config duy nhất, đọc từ `.env`.

### 1.9. Requirements không khớp với code

- **Vấn đề:**
  - `requirements.txt` liệt kê `flask`, `flask-cors` nhưng code dùng **FastAPI** + **uvicorn**
  - Thiếu `fastapi`, `uvicorn`, `pydantic` trong requirements
  - Tài liệu `API_GUIDE.md` mô tả Flask nhưng code thực tế là FastAPI
- **Hệ quả:** Clone repo → `pip install -r requirements.txt` → thiếu dependency → app không chạy được.

---

## 2. Vấn đề về product-market fit

### 2.1. Vấn đề thực tế của sinh viên
Từ kinh nghiệm, sinh viên thường hỏi:
- "Môn X thầy Y thi thế nào?" 
- "Đăng ký học phần khi nào?"
- "Phòng lab A203 ở tòa nào?"

Nhiều câu hỏi này **không có trong Facebook group** hoặc thông tin **bị lẫn với rác**.

**Đề xuất:** Kết hợp thêm:
- Crawl từ trang thông tin chính thức của trường
- Manual curated FAQ từ ban cán sự lớp
- Structured data (lịch học, sơ đồ trường) → dùng SQL/graph query, không phải RAG

---

### 2.2. Feedback loop
- Người dùng hỏi → bot trả lời → **không biết câu trả lời có đúng/hữu ích không**
- Cần có thumbs up/down, hoặc "Có tìm được thông tin không?" để improve model

---

## 3. Đánh giá tổng quan

**Điểm số: 6/10**

| Tiêu chí               | Điểm  | Ghi chú                                                    |
|------------------------|-------|-------------------------------------------------------------|
| Technical foundation   | 7/10  | RAG pipeline đúng hướng, hybrid search tốt, nhưng thiếu optimization |
| Data quality           | 4/10  | Chưa có cleaning/filtering pipeline                         |
| Code quality & security| 4/10  | Hardcode secrets, config phân tán, requirements sai         |
| UX                     | 5/10  | Functional nhưng thiếu polish, thiếu feedback mechanism     |
| Scalability            | 5/10  | Load all embeddings vào RAM không scale; chưa tận dụng Qdrant search API |
| Documentation          | 5/10  | Có docs nhưng nội dung không khớp thực tế (Flask vs FastAPI)|

---

## 4. Roadmap ưu tiên

**Phase 0 — Fix nền tảng (trước khi làm gì khác):**
1. Loại bỏ hardcode secrets, gộp config thành 1 nguồn duy nhất
2. Sửa `requirements.txt` (thêm FastAPI/uvicorn, bỏ Flask)
3. Cập nhật `API_GUIDE.md` cho đúng thực tế
4. Tạo test set 20-30 câu hỏi mẫu của sinh viên

**Phase 1 — Critical:**
1. Data cleaning pipeline (remove emoji spam, normalize text, dedup)
2. Improve prompt engineering (thêm persona, citation, viết có dấu)
3. Add MMR for diversity in retrieval
4. A/B test các tham số (dense_weight, sparse_weight, top_k) dựa trên test set

**Phase 2 — Nice to have:**
1. Tận dụng Qdrant search API thay vì load hết vào RAM
2. Recency boosting cho temporal queries
3. Feedback collection system (thumbs up/down)
4. Logging & dashboard để monitor query quality

---

## 5. Lời khuyên cuối

Chatbot có foundation tốt (hybrid search, Qdrant, Gemini), nhưng **"garbage in, garbage out"** — nếu data từ Facebook không được clean kỹ, RAG retrieval sẽ trả về rác, LLM cũng generate rác.

Ngoài data quality, cần **ưu tiên fix ngay các vấn đề bảo mật** (hardcode secrets) và **đồng bộ tài liệu/config** để tránh lỗi khi deploy hoặc khi có người mới tham gia dự án.

**Ưu tiên số 1:** Fix Phase 0 trước, sau đó đầu tư vào data quality pipeline. Test thử với 100 câu hỏi thật từ sinh viên để thấy pain points.

---

*Tài liệu được tạo dựa trên đánh giá repo Socia-crawler-chatbot. Xem thêm [Suggestions.md](./Suggestions.md) cho các đề xuất cải thiện chi tiết.*