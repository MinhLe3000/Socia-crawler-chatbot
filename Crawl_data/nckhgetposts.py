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
POSTS_COLLECTION = os.getenv("MONGO_POSTS_COLLECTION")

if not ACCESS_TOKEN:
    raise Exception("❌ Missing FB_ACCESS_TOKEN in .env")

BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"
REACTION_TYPES = ["LIKE", "LOVE", "HAHA", "WOW", "SAD", "ANGRY"]

# =====================================================
# MONGODB
# =====================================================
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
posts_col = db[COLLECTION_NAME]

# =====================================================
# GET NEW POSTS (INCREMENTAL)
# =====================================================
def get_new_posts():
    new_posts = []
    url = f"{BASE_URL}/{GROUP_ID}/feed"
    params = {
        "fields": (
            "id,"
            "permalink_url,"
            "from{id,name},"
            "full_picture,"
            "message,"
            "created_time,"
            "updated_time,"
            "comments.summary(true),"
            "shares"
        ),
        "limit": 10,          # an toàn cho group
        "access_token": ACCESS_TOKEN
    }

    while url:
        res = requests.get(url, params=params)
        data = res.json()

        if "error" in data:
            raise Exception(data["error"])

        for post in data.get("data", []):
            post_id = post["id"]

            # DỪNG KHI GẶP POST CŨ
            if posts_col.find_one({"_id": post_id}):
                print(f"Reached old post {post_id}. Stop crawling.")
                return new_posts

            new_posts.append(post)

        url = data.get("paging", {}).get("next")
        params = None
        time.sleep(1)   # tránh bị drop bài

    return new_posts

# =====================================================
# GET REACTION COUNT
# =====================================================
def get_reaction_count(post_id, reaction_type):
    url = f"{BASE_URL}/{post_id}"
    params = {
        "fields": f"reactions.type({reaction_type}).summary(true)",
        "access_token": ACCESS_TOKEN
    }

    res = requests.get(url, params=params)
    data = res.json()

    return (
        data.get("reactions", {})
            .get("summary", {})
            .get("total_count", 0)
    )

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    new_posts = get_new_posts()
    print(f"\nFound {len(new_posts)} new posts\n")

    for post in new_posts:
        post_id = post["id"]

        author = post.get("from")
        author_data = None
        if author:
            author_data = {
                "id": author.get("id"),
                "name": author.get("name")
            }

        reactions = {}
        for r in REACTION_TYPES:
            reactions[r] = get_reaction_count(post_id, r)
            time.sleep(0.3)

        document = {
            "_id": post_id,
            "group_id": GROUP_ID,
            "permalink_url": post.get("permalink_url"),
            "author": author_data,
            "message": post.get("message"),
            "created_time": post.get("created_time"),
            "updated_time": post.get("updated_time"),
            "full_picture": post.get("full_picture"),
            "comments_count": (
                post.get("comments", {})
                    .get("summary", {})
                    .get("total_count", 0)
            ),
            "shares_count": post.get("shares", {}).get("count", 0),
            "reactions": reactions,
            "fetched_at": datetime.utcnow()
        }

        posts_col.update_one(
            {"_id": post_id},
            {"$set": document},
            upsert=True
        )

        print(f"Saved post {post_id}")
        time.sleep(0.5)

    print("\nDONE.")
