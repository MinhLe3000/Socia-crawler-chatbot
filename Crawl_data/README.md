# 📊 Hướng Dẫn Lấy Dữ Liệu từ Facebook Group

Folder này chứa các script để thu thập dữ liệu từ Facebook Group (bài viết và bình luận) và lưu vào MongoDB.

## 📋 Tổng Quan

Hệ thống gồm 2 script chính:
- **`nckhgetposts.py`** - Lấy bài viết mới từ Facebook Group
- **`nckhgetcmt.py`** - Lấy bình luận (comments) và trả lời (replies) của bài viết

Đặc điểm:
- ✅ Lấy dữ liệu **incremental** (chỉ lấy dữ liệu mới, không trùng)
- ✅ Tự động lưu vào **MongoDB**
- ✅ Có độ trễ (delay) để tránh bị Facebook throttle
- ✅ Xử lý phản ứng (reactions), bình luận, trả lời có cấu trúc

---

## 🔧 Cài Đặt

### 1. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies cần thiết:**
- `requests` - Gọi Facebook Graph API
- `pymongo` - Kết nối MongoDB
- `python-dotenv` - Đọc biến môi trường từ file `.env`

### 2. Cấu Hình File `.env`

File `.env` đã có sẵn, bạn chỉ cần điền các giá trị vào:

```env
# =======================
# FACEBOOK CONFIG
# =======================
FB_ACCESS_TOKEN=your_access_token_here
FB_GROUP_ID=your_group_id_here
FB_GRAPH_VERSION=v24.0

# =======================
# MONGODB CONFIG
# =======================
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=chatbotNeu
MONGO_POSTS_COLLECTION=posts
MONGO_COMMENTS_COLLECTION=comments
```

**Cần lấy gì?**

| Biến | Mô Tả | Ví Dụ |
|------|-------|-------|
| `FB_ACCESS_TOKEN` | Facebook User Access Token (v24.0+) | Lấy từ Facebook Developer Portal |
| `FB_GROUP_ID` | ID của group Facebook | Ví dụ: `123456789` |
| `FB_GRAPH_VERSION` | Phiên bản Facebook Graph API | `v24.0` |
| `MONGO_URI` | Địa chỉ MongoDB | `mongodb://localhost:27017` hoặc MongoDB Atlas URI |
| `MONGO_DB_NAME` | Tên database MongoDB | `chatbotNeu` |
| `MONGO_POSTS_COLLECTION` | Collection lưu posts | `posts` (mặc định) |
| `MONGO_COMMENTS_COLLECTION` | Collection lưu comments | `comments` (mặc định) |

---

## 🚀 Cách Chạy

### Script 1: Lấy Bài Viết (`nckhgetposts.py`)

```bash
python nckhgetposts.py
```

**Chức năng:**
- Lấy 10 bài viết mới nhất từ group
- Lấy số lượng từng loại reaction: LIKE, LOVE, HAHA, WOW, SAD, ANGRY
- Lấy số lượng bình luận, shares
- Tự động dừng khi gặp bài cũ (đã lưu)
- Lưu vào collection `posts` trong MongoDB

**Dữ liệu được lưu:**
```json
{
  "_id": "post_id",
  "group_id": "group_id",
  "permalink_url": "link_to_post",
  "author": {
    "id": "author_id",
    "name": "author_name"
  },
  "message": "nội dung bài viết",
  "created_time": "2024-01-01T12:00:00",
  "updated_time": "2024-01-01T12:00:00",
  "full_picture": "url_ảnh",
  "comments_count": 10,
  "shares_count": 5,
  "reactions": {
    "LIKE": 50,
    "LOVE": 5,
    "HAHA": 2,
    "WOW": 1,
    "SAD": 0,
    "ANGRY": 0
  },
  "fetched_at": "2024-01-15T10:00:00"
}
```

### Script 2: Lấy Bình Luận (`nckhgetcmt.py`)

```bash
python nckhgetcmt.py
```

**Chức năng:**
- Lấy tất cả bình luận từ mỗi bài viết (20 bình luận/page)
- Lấy tất cả trả lời của mỗi bình luận (replies)
- Lấy thông tin reactions của bình luận
- Tự động dừng khi gặp bình luận cũ
- Lưu vào collection `comments` trong MongoDB

**Dữ liệu Root Comments:**
```json
{
  "_id": "comment_id",
  "post_id": "post_id",
  "parent_comment_id": null,
  "permalink_url": "link_to_post",
  "message": "nội dung bình luận",
  "like_count": 5,
  "reactions_count": 3,
  "created_time": "2024-01-01T12:00:00",
  "fetched_at": "2024-01-15T10:00:00"
}
```

**Dữ liệu Replies (Trả lời):**
```json
{
  "_id": "reply_id",
  "post_id": "post_id",
  "parent_comment_id": "comment_id",
  "permalink_url": "link_to_post",
  "message": "nội dung trả lời",
  "like_count": 2,
  "reactions_count": 1,
  "created_time": "2024-01-01T12:00:00",
  "fetched_at": "2024-01-15T10:00:00"
}
```

---

## 📝 Quy Trình Lấy Dữ Liệu Chuẩn

1. **Chạy script 1 lấy posts:**
   ```bash
   python nckhgetposts.py
   ```
   Chờ cho đến khi hoàn tất tất cả bài viết mới.

2. **Chạy script 2 lấy comments:**
   ```bash
   python nckhgetcmt.py
   ```
   Chờ cho đến khi hoàn tất tất cả bình luận.

---

## ⚙️ Các Tham Số Quan Trọng

| Tham Số | Vị Trí | Ý Nghĩa |
|---------|--------|---------|
| `limit: 10` | `nckhgetposts.py` | Số bài viết lấy mỗi lần (giới hạn để tránh throttle) |
| `limit: 20` | `nckhgetcmt.py` | Số bình luận lấy mỗi page |
| `time.sleep(1)` | `nckhgetposts.py` | Độ trễ giữa các request posts (tránh bị block) |
| `time.sleep(0.5)` | `nckhgetcmt.py` | Độ trễ giữa các request comments |
| `time.sleep(0.3)` | `nckhgetcmt.py` | Độ trễ giữa các request replies |

---

## 🔍 Cơ Chế Incremental (Tránh Lấy Trùng)

### Đối với Posts:
- Khi gặp post đã tồn tại trong database → dừng crawl ngay
- Giả định các bài viết mới luôn ở đầu

### Đối với Comments:
- Khi gặp comment đã tồn tại → dừng crawl comment root
- Replies được kiểm tra từng cái để tránh trùng

---

## 🚨 Xử Lý Lỗi Phổ Biến

| Lỗi | Nguyên Nhân | Giải Pháp |
|-----|-----------|----------|
| `Missing FB_ACCESS_TOKEN` | Không có token trong `.env` | Kiểm tra file `.env` và thêm token |
| `Facebook API Error` | Token hết hạn hoặc permissions không đủ | Tạo token mới hoặc kiểm tra permissions |
| `MongoDB Connection Error` | Không kết nối được MongoDB | Kiểm tra `MONGO_URI` và MongoDB running |
| `Rate Limited` | Gửi request quá nhanh | Tăng giá trị `time.sleep()` |

---

## 📊 Kiểm Tra Dữ Liệu

Dùng MongoDB Client để kiểm tra dữ liệu đã lưu:

```bash
# Xem số posts
db.posts.countDocuments()

# Xem số comments
db.comments.countDocuments()

# Xem 1 post
db.posts.findOne()

# Xem comments của 1 post
db.comments.find({"post_id": "post_id_here"}).limit(5)
```

---

## 📌 Lưu Ý

- **Access Token hết hạn**: Facebook access token có thể hết hạn, cần tạo lại định kỳ
- **Permissions**: Token cần có permissions: `groups_access_member_info`, `pages_read_engagement`, `pages_show_list`
- **Rate Limiting**: Facebook giới hạn API calls, nếu bị throttle hãy tăng delay
- **Data Freshness**: Chạy script định kỳ để lấy dữ liệu mới

---

## 💡 Mẹo Sử Dụng

```bash
# Chạy cả 2 script liên tiếp
python nckhgetposts.py && python nckhgetcmt.py

# Hoặc chạy với logging
python nckhgetposts.py > nckhgetposts.log 2>&1
python nckhgetcmt.py > nckhgetcmt.log 2>&1

# Chạy định kỳ (ví dụ trên Linux/Mac)
0 */6 * * * cd /path/to/folder && python nckhgetposts.py && python nckhgetcmt.py
```

---

**Tác giả**: Nhóm nghiên cứu  
**Cập nhật lần cuối**: Tháng 2 năm 2026
