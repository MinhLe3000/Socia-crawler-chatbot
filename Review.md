### ❌ **Vấn đề nghiêm trọng**

#### 1. **Thiếu preprocessing & cleaning data** -> Optional
- Code của bạn chỉ `.strip()` message và thay bằng `[NO_MESSAGE]` nếu rỗng
- **Thực tế**: Posts/comments trên Facebook rất nhiễu:
  - Emoji spam (🔥🔥🔥, ❤️❤️❤️)
  - Link rác, mã giới thiệu
  - Chữ viết tắt teen code ("ông nội", "mik", "vs", "dc")
  - Duplicate content (copy-paste)
  - Comments 1-2 từ vô nghĩa ("oke", "đã xem", ".")

➡️ **Hậu quả**: RAG retrieval sẽ trả về nhiều kết quả vô nghĩa, LLM sẽ bị nhiễu.

**Giải pháp cần có**:
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

#### 2. **Không có document ranking/filtering thông minh**
- Bạn chỉ lấy top-5 docs dựa trên similarity score
- **Thực tế**: Trong group sinh viên, 1 topic nóng có thể có 500 comments tương tự nhau ("mình cũng vậy", "đúng rồi")

➡️ **Hậu quả**: Top-5 kết quả đều là comments chung chung, thiếu thông tin đa dạng.

**Giải pháp**:
- MMR (Maximal Marginal Relevance) để đảm bảo diversity
- Prioritize posts > comments (posts thường có info density cao hơn)
- Clustering để nhóm các comments tương tự, chỉ lấy representative

---

#### 3. **Prompt engineering quá đơn giản** -> Backend, ko phải embedding
```python
"Ban la tro ly tra loi cau hoi dua tren thong tin duoc cung cap.\n"
"Neu khong tim duoc cau tra loi trong context thi noi ro la khong ro.\n\n"
```

**Vấn đề**:
- Không có instruction về cách tổng hợp thông tin từ nhiều nguồn
- Không yêu cầu cite sources
- Không handle trường hợp conflicting information
- Không có persona/tone guidance (sinh viên thích câu trả lời ngắn gọn, thân thiện)

**Prompt cải thiện**:
```python
"""Bạn là trợ lý AI của nhóm sinh viên, giúp tóm tắt thông tin từ các bài đăng và bình luận.

NHIỆM VỤ:
1. Đọc kỹ các documents được cung cấp
2. Tổng hợp thông tin theo thứ tự ưu tiên: posts gốc → comments có nhiều tương tác
3. Nếu có ý kiến trái chiều, trình bày cả hai phía
4. Trả lời ngắn gọn, dễ hiểu (2-3 đoạn văn)
5. LUÔN trích dẫn nguồn: "[DOC X] cho biết..."

Nếu không tìm thấy thông tin: "Mình không thấy thông tin về vấn đề này trong nhóm. Bạn có thể hỏi cụ thể hơn không?"
"""
```

---

#### 4. **Thiếu evaluation metrics**
- Bạn không có cách nào đo lường chất lượng retrieval/generation
- Làm sao biết hybrid search (0.7 dense + 0.3 sparse) là optimal?

**Cần có**:
- Test set với 20-30 câu hỏi mẫu của sinh viên
- Metrics: Recall@K, MRR, nDCG cho retrieval
- Human evaluation cho answer quality (1-5 scale)

---

#### 5. **Không handle temporal information**
```python
"source": {
    "post_id": post_id,
    "permalink_url": post.get("permalink_url"),
},
"created_time": post.get("created_time"),  # ← Chưa dùng trong retrieval
```

**Vấn đề**: Thông tin về lịch thi, sự kiện, deadline... cần ưu tiên bài post gần đây.

➡️ Nên có **recency boosting**: posts trong 7 ngày qua được cộng thêm điểm.

---

#### 6. **Performance concerns** -> Đã áp dụng vector db Qdrant
```python
self.embeddings = np.stack(emb_list, axis=0)  # Load ALL vào RAM
```

**Vấn đề**: 
- Giả sử 10,000 documents × 1024 dims × 4 bytes = ~40MB (OK)
- Nhưng nếu scale lên 100K docs = 400MB
- Nếu có nhiều concurrent users, mỗi request đều tính toán cosine similarity trên toàn bộ corpus

**Giải pháp**: 
- Sử dụng FAISS/Annoy cho approximate nearest neighbor (nhanh hơn 10-100x)
- Hoặc dùng MongoDB Atlas Vector Search (đã support native vector search)

---

### ⚠️ **Vấn đề về product-market fit**

#### 1. **Vấn đề thực tế của sinh viên**
Từ kinh nghiệm, sinh viên thường hỏi:
- "Môn X thầy Y thi thế nào?" 
- "Đăng ký học phần khi nào?"
- "Phòng lab A203 ở tòa nào?"

➡️ Nhiều câu hỏi này **không có trong Facebook group** hoặc thông tin **bị lẫn với rác**.

**Đề xuất**: Kết hợp thêm:
- Crawl từ trang thông tin chính thức của trường
- Manual curated FAQ từ ban cán sự lớp
- Structured data (lịch học, sơ đồ trường) → dùng SQL/graph query, không phải RAG

---

#### 2. **Feedback loop**
- Người dùng hỏi → bot trả lời → **không biết câu trả lời có đúng/hữu ích không**
- Cần có thumbs up/down, hoặc "Có tìm được thông tin không?" để improve model

---

### 🎯 **Đánh giá tổng quan**

**Điểm số: 6/10**

- **Technical foundation**: 7/10 (RAG pipeline đúng, nhưng thiếu optimization)
- **Data quality**: 4/10 (chưa có cleaning/filtering)
- **UX**: 5/10 (functional nhưng thiếu polish)
- **Scalability**: 5/10 (load all embeddings vào RAM không scale)

---

### 📝 **Roadmap ưu tiên**

**Phase 0 (Trước khi làm gì khác)**:
1. ✅ Crawl thử 500-1000 posts/comments từ 1 group sinh viên thật
2. ✅ Phân tích xem: % nào là noise, % nào useful
3. ✅ Tạo test set 20 câu hỏi thật của sinh viên

**Phase 1 (Critical)**:
1. Data cleaning pipeline (remove emoji spam, normalize text)
2. Improve prompt engineering + add citation
3. Add MMR for diversity in retrieval
4. A/B test các tham số (dense_weight, sparse_weight, top_k)

**Phase 2 (Nice to have)**:
1. FAISS for faster similarity search
2. Recency boosting cho temporal queries
3. Feedback collection system
4. Dashboard để monitor query quality

---

### 💡 **Lời khuyên cuối**

Chatbot của bạn có foundation tốt, nhưng **"garbage in, garbage out"** - nếu data từ Facebook không được clean kỹ, RAG retrieval sẽ trả về rác, LLM cũng generate rác.

**Ưu tiên số 1**: Đầu tư vào data quality pipeline trước khi optimize model/infrastructure. Test thử với 100 câu hỏi thật từ sinh viên để thấy pain points.