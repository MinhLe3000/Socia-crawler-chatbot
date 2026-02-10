import os
import time
import requests
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# =====================================================
# LOAD ENV
# =====================================================
load_dotenv()

ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
GROUP_ID = os.getenv("FB_GROUP_ID")
GRAPH_VERSION = os.getenv("FB_GRAPH_VERSION")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")
POSTS_COLLECTION = os.getenv("MONGO_POSTS_COLLECTION", "posts")
COMMENTS_COLLECTION = os.getenv("MONGO_COMMENTS_COLLECTION", "comments")

if not ACCESS_TOKEN:
    raise Exception("❌ Missing FB_ACCESS_TOKEN in .env")

BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

# =====================================================
# MONGODB
# =====================================================
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
posts_col = db[POSTS_COLLECTION]
comments_col = db[COMMENTS_COLLECTION]

# =====================================================
# GET NEW ROOT COMMENTS (20 / PAGE, INCREMENTAL)
# =====================================================
def get_new_root_comments(post_id, permalink_url):
    new_comments = []
    url = f"{BASE_URL}/{post_id}/comments"
    params = {
        "fields": (
            "id,"
            "message,"
            "like_count,"
            "created_time,"
            "reactions.summary(true)"
        ),
        "limit": 20,
        "access_token": ACCESS_TOKEN
    }

    while url:
        res = requests.get(url, params=params).json()

        if "error" in res:
            raise Exception(res["error"])

        for c in res.get("data", []):
            comment_id = c["id"]

            # 🚨 DỪNG KHI GẶP COMMENT CŨ
            if comments_col.find_one({"_id": comment_id}):
                print(f"Reached old comment {comment_id} → stop")
                return new_comments

            doc = {
                "_id": comment_id,
                "post_id": post_id,
                "parent_comment_id": None,
                "permalink_url": permalink_url,
                "message": c.get("message"),
                "like_count": c.get("like_count", 0),
                "reactions_count": (
                    c.get("reactions", {})
                     .get("summary", {})
                     .get("total_count", 0)
                ),
                "created_time": c.get("created_time"),
                "fetched_at": datetime.utcnow()
            }

            new_comments.append(doc)

        url = res.get("paging", {}).get("next")
        params = None
        time.sleep(0.5)

    return new_comments

# =====================================================
# GET REPLIES OF ONE COMMENT (20 / PAGE)
# =====================================================
def get_replies(comment_id, post_id, permalink_url):
    replies = []
    url = f"{BASE_URL}/{comment_id}/comments"
    params = {
        "fields": (
            "id,"
            "message,"
            "like_count,"
            "created_time,"
            "reactions.summary(true)"
        ),
        "limit": 20,
        "access_token": ACCESS_TOKEN
    }

    while url:
        res = requests.get(url, params=params).json()

        if "error" in res:
            raise Exception(res["error"])

        for r in res.get("data", []):
            reply_id = r["id"]

            # reply cũng không lưu trùng
            if comments_col.find_one({"_id": reply_id}):
                continue

            replies.append({
                "_id": reply_id,
                "post_id": post_id,
                "parent_comment_id": comment_id,
                "permalink_url": permalink_url,
                "message": r.get("message"),
                "like_count": r.get("like_count", 0),
                "reactions_count": (
                    r.get("reactions", {})
                     .get("summary", {})
                     .get("total_count", 0)
                ),
                "created_time": r.get("created_time"),
                "fetched_at": datetime.utcnow()
            })

        url = res.get("paging", {}).get("next")
        params = None
        time.sleep(0.5)

    return replies

# =====================================================
# MAIN PROCESS
# =====================================================
if __name__ == "__main__":
    posts = posts_col.find({}, {"_id": 1, "permalink_url": 1})

    for post in posts:
        post_id = post["_id"]
        permalink = post.get("permalink_url")

        print(f"\n📌 Crawling comments for post {post_id}")

        # =============================
        # ROOT COMMENTS
        # =============================
        new_comments = get_new_root_comments(post_id, permalink)

        for c in new_comments:
            comments_col.update_one(
                {"_id": c["_id"]},
                {"$set": c},
                upsert=True
            )

            # =============================
            # REPLIES
            # =============================
            replies = get_replies(c["_id"], post_id, permalink)
            for r in replies:
                comments_col.update_one(
                    {"_id": r["_id"]},
                    {"$set": r},
                    upsert=True
                )

            time.sleep(0.3)

        print(f"   ➜ Saved {len(new_comments)} new root comments")
        time.sleep(1)

    print("\nDONE. Incremental comment crawl finished.")
