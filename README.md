# Facebook Group Data Collection Module

## 📋 Table of Contents

1. [Overview](#overview)
2. [Purpose in System Architecture](#purpose-in-system-architecture)
3. [Data Pipeline](#data-pipeline)
4. [File Structure and Roles](#file-structure-and-roles)
5. [Data Flow](#data-flow)
6. [Dependencies and Environment](#dependencies-and-environment)
7. [Setup and Installation](#setup-and-installation)
8. [Usage Guide](#usage-guide)
9. [Output Data Format](#output-data-format)
10. [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
11. [Security Considerations](#security-considerations)

---

## 🎯 Overview

This module is responsible for **collecting and ingesting data from Facebook Groups** using the Facebook Graph API. It serves as the **data ingestion layer** for a RAG (Retrieval-Augmented Generation) chatbot system that answers questions based on Facebook group discussions.

The system implements an **incremental crawling strategy** to efficiently collect new posts and comments without re-processing existing data, making it suitable for continuous data collection workflows.

---

## 🏗️ Purpose in System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Chatbot System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐  │
│  │   Facebook   │ ───> │  Data        │ ───> │   RAG    │  │
│  │   Group      │      │  Collection  │      │  Chatbot │  │
│  │              │      │  (This Module)│      │          │  │
│  └──────────────┘      └──────────────┘      └──────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Role**: This folder contains scripts that:
1. **Extract** posts and comments from Facebook Groups via Graph API
2. **Store** raw data in MongoDB collections
3. **Export** data to CSV format for analysis and backup
4. **Feed** the downstream RAG chatbot system with structured knowledge

The collected data flows into the `RAG_chatbot` module, where it is:
- Normalized into a knowledge base
- Embedded using BGE-M3 model
- Indexed for semantic search
- Used to answer user queries via Gemini AI

---

## 🔄 Data Pipeline

### Step-by-Step Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE OVERVIEW                        │
└─────────────────────────────────────────────────────────────────┘

1. DATA SOURCE
   └─> Facebook Group (via Graph API)
       └─> Group ID: 1170189375194877

2. DATA INGESTION
   ├─> Step 1: Fetch Posts (getpost.py / nckhgetposts.py)
   │   └─> API Endpoint: /{group_id}/feed
   │       └─> Fields: id, message, author, reactions, comments_count, etc.
   │
   └─> Step 2: Fetch Comments (getcomments.py / nckhgetcmt.py)
       └─> API Endpoint: /{post_id}/comments
           └─> Recursive: Root comments + Replies

3. DATA STORAGE
   └─> MongoDB Collections
       ├─> Collection: "posts"
       │   └─> Document Schema:
       │       {
       │         _id: post_id,
       │         group_id: string,
       │         message: string,
       │         author: {id, name},
       │         reactions: {LIKE, LOVE, HAHA, WOW, SAD, ANGRY},
       │         comments_count: int,
       │         shares_count: int,
       │         created_time: datetime,
       │         permalink_url: string
       │       }
       │
       └─> Collection: "comments"
           └─> Document Schema:
               {
                 _id: comment_id,
                 post_id: string,
                 parent_comment_id: string | null,
                 message: string,
                 like_count: int,
                 reactions_count: int,
                 created_time: datetime,
                 permalink_url: string
               }

4. DATA EXPORT (Optional)
   └─> CSV Files
       ├─> chatbotNeu.posts.csv
       ├─> chatbotNeu.comments.csv
       └─> chatbotNeu.knowledge_base.csv (with embeddings)

5. DOWNSTREAM PROCESSING
   └─> RAG Chatbot Module
       ├─> Normalize posts/comments → knowledge_base
       ├─> Generate embeddings (BGE-M3)
       └─> Index for semantic search
```

### Detailed Pipeline Stages

#### Stage 1: Post Collection
- **Script**: `getpost.py` or `nckhgetposts.py`
- **Method**: Incremental pagination
- **Strategy**: Stop when encountering existing post in database
- **Rate Limiting**: 1 second delay between API calls
- **Data Retrieved**:
  - Post metadata (ID, permalink, timestamps)
  - Author information
  - Post content (message)
  - Engagement metrics (reactions, comments, shares)
  - Media URLs (full_picture)

#### Stage 2: Comment Collection
- **Script**: `getcomments.py` or `nckhgetcmt.py`
- **Method**: Hierarchical traversal
- **Strategy**: 
  - Fetch root comments (top-level)
  - For each comment, fetch replies recursively
  - Stop when encountering existing comments
- **Rate Limiting**: 0.5 seconds between API calls
- **Data Retrieved**:
  - Comment content and metadata
  - Parent-child relationships (for threaded discussions)
  - Engagement metrics (likes, reactions)

#### Stage 3: Data Preprocessing
- **No explicit preprocessing** in this module
- Raw data is stored as-is from Facebook API
- Downstream RAG module handles:
  - Text normalization
  - Chunking (if needed)
  - Embedding generation

#### Stage 4: Storage
- **Primary Storage**: MongoDB (NoSQL document database)
- **Backup Format**: CSV files (for portability and analysis)
- **Incremental Updates**: Uses `upsert` operations to avoid duplicates

---

## 📁 File Structure and Roles

```
Lấy dữ liệu/
│
├── getpost.py                    # Post collection script (uses .env)
├── nckhgetposts.py               # Post collection script (uses .env)
├── getcomments.py                # Comment collection script (hardcoded config)
├── nckhgetcmt.py                 # Comment collection script (hardcoded config)
│
├── chatbotNeu.posts.csv          # Exported posts data
├── chatbotNeu.comments.csv       # Exported comments data
├── chatbotNeu.knowledge_base.csv # Knowledge base with embeddings (3.7MB)
│
├── facebook_group_posts.json     # Sample JSON data structure
│
└── README.md                     # This documentation
```

### File Descriptions

#### 1. `getpost.py` / `nckhgetposts.py`
**Purpose**: Collect new posts from Facebook Group

**Key Features**:
- Uses environment variables (`.env` file) for configuration
- Incremental crawling (stops at first existing post)
- Fetches detailed reaction counts (6 types)
- Stores data in MongoDB `posts` collection

**Configuration**:
- Requires `.env` file with:
  - `FB_ACCESS_TOKEN`: Facebook Graph API access token
  - `FB_GROUP_ID`: Target Facebook Group ID
  - `FB_GRAPH_VERSION`: API version (default: v24.0)
  - `MONGO_URI`: MongoDB connection string
  - `MONGO_DB_NAME`: Database name
  - `MONGO_COLLECTION`: Collection name (usually "posts")

**Main Functions**:
- `get_new_posts()`: Fetches new posts via pagination
- `get_reaction_count()`: Gets count for specific reaction type

#### 2. `getcomments.py` / `nckhgetcmt.py`
**Purpose**: Collect comments and replies for existing posts

**Key Features**:
- Hardcoded credentials (⚠️ security risk)
- Processes all posts from MongoDB
- Hierarchical comment structure (root + replies)
- Stores data in MongoDB `comments` collection

**Configuration**:
- Hardcoded in script:
  - `ACCESS_TOKEN`: Facebook API token
  - `GROUP_ID`: Facebook Group ID
  - `MONGO_URI`: MongoDB connection string
  - `DB_NAME`: Database name
  - Collections: "posts" and "comments"

**Main Functions**:
- `get_new_root_comments()`: Fetches top-level comments
- `get_replies()`: Fetches replies for a specific comment

**Differences Between Versions**:
- `nckhgetcmt.py`: Uses `chatbotNeu` database
- `getcomments.py`: Uses `Postandcmt` database

#### 3. CSV Export Files

**`chatbotNeu.posts.csv`**:
- Exported posts data
- Columns: `_id`, `author`, `message`, `created_time`, `reactions.*`, `comments_count`, `shares_count`, etc.
- Format: CSV with comma delimiter

**`chatbotNeu.comments.csv`**:
- Exported comments data
- Columns: `_id`, `post_id`, `parent_comment_id`, `message`, `like_count`, `created_time`, etc.
- Format: CSV with comma delimiter

**`chatbotNeu.knowledge_base.csv`**:
- Processed knowledge base with embeddings
- Contains normalized text from posts/comments
- Includes dense embeddings (1024 dimensions) from BGE-M3 model
- Generated by downstream RAG module

#### 4. `facebook_group_posts.json`
- Sample JSON file showing expected data structure
- Useful for understanding API response format
- Contains example posts with all fields

---

## 🔀 Data Flow Between Scripts

```
┌──────────────────────────────────────────────────────────────┐
│                    EXECUTION WORKFLOW                         │
└──────────────────────────────────────────────────────────────┘

PHASE 1: Initial Data Collection
─────────────────────────────────
1. Run getpost.py (or nckhgetposts.py)
   │
   ├─> Connects to Facebook Graph API
   ├─> Fetches posts from group feed
   ├─> Checks MongoDB for existing posts
   ├─> Stops at first existing post (incremental)
   └─> Saves new posts → MongoDB "posts" collection
       │
       └─> Output: New posts in database

2. Run getcomments.py (or nckhgetcmt.py)
   │
   ├─> Reads all posts from MongoDB "posts" collection
   ├─> For each post:
   │   ├─> Fetches root comments from API
   │   ├─> Checks MongoDB for existing comments
   │   ├─> Stops at first existing comment (incremental)
   │   ├─> For each new comment:
   │   │   └─> Fetches replies recursively
   │   └─> Saves comments → MongoDB "comments" collection
   └─> Output: New comments and replies in database

PHASE 2: Data Export (Optional)
────────────────────────────────
3. Export MongoDB data to CSV
   │
   ├─> Use MongoDB export tools or custom script
   ├─> Export "posts" → chatbotNeu.posts.csv
   └─> Export "comments" → chatbotNeu.comments.csv

PHASE 3: Downstream Processing
───────────────────────────────
4. RAG Chatbot Module (in ../RAG_chatbot/)
   │
   ├─> scripts/index_mongo.py
   │   └─> Reads posts/comments from MongoDB
   │   └─> Normalizes into knowledge_base collection
   │
   ├─> scripts/embed_bge_m3.py
   │   └─> Generates embeddings for knowledge_base
   │
   └─> chat_cli.py
       └─> Uses knowledge_base for RAG retrieval
```

### Incremental Update Strategy

Both scripts implement **incremental crawling**:

1. **Posts**: When fetching posts, the script checks each post ID against MongoDB. Upon encountering an existing post, it stops pagination and returns only new posts.

2. **Comments**: When fetching comments, the script:
   - Checks each comment ID against MongoDB
   - Stops fetching root comments when encountering an existing one
   - Skips existing replies (continues fetching others)
   - Assumes posts are processed in chronological order (newest first)

**Benefits**:
- Efficient: Only processes new data
- Cost-effective: Reduces API calls
- Safe: Can be run repeatedly without duplicates

**Limitations**:
- Assumes posts are fetched in reverse chronological order
- If a post is deleted from Facebook, it won't be detected
- Comments added to old posts require full comment scan

---

## 📦 Dependencies and Environment

### Required Python Packages

```python
requests          # HTTP library for API calls
pymongo          # MongoDB driver
python-dotenv    # Environment variable management (for getpost.py)
datetime         # Date/time handling (built-in)
time             # Rate limiting delays (built-in)
```

### Installation

```bash
pip install requests pymongo python-dotenv
```

### Environment Variables

#### For `getpost.py` / `nckhgetposts.py`:

Create a `.env` file in the project root:

```env
# Facebook Graph API Configuration
FB_ACCESS_TOKEN=your_facebook_access_token_here
FB_GROUP_ID=1170189375194877
FB_GRAPH_VERSION=v24.0

# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=AppName
MONGO_DB_NAME=your_database_name
MONGO_COLLECTION=posts
```

#### For `getcomments.py` / `nckhgetcmt.py`:

**⚠️ WARNING**: These scripts use hardcoded credentials. Update the following variables in the script:

```python
ACCESS_TOKEN = "your_token_here"
GROUP_ID = "1170189375194877"
MONGO_URI = "your_mongodb_uri"
DB_NAME = "your_database_name"
```

### Facebook Graph API Requirements

1. **Access Token**:
   - Requires Facebook App with appropriate permissions
   - Permissions needed: `groups_access_member_info`, `read_insights`
   - Token must have access to the target group

2. **API Version**:
   - Currently using `v24.0`
   - Check [Facebook Graph API Changelog](https://developers.facebook.com/docs/graph-api/changelog) for updates

3. **Rate Limits**:
   - Facebook enforces rate limits per app/user
   - Scripts include delays to avoid hitting limits
   - If rate limited, increase `time.sleep()` values

### MongoDB Requirements

1. **Database Structure**:
   ```
   Database: chatbotNeu (or Postandcmt)
   ├── Collection: posts
   │   └── Documents: {_id, message, author, reactions, ...}
   └── Collection: comments
       └── Documents: {_id, post_id, parent_comment_id, message, ...}
   ```

2. **Indexes** (Recommended):
   ```javascript
   // For posts collection
   db.posts.createIndex({_id: 1})  // Already unique by default
   db.posts.createIndex({created_time: -1})  // For chronological queries
   
   // For comments collection
   db.comments.createIndex({_id: 1})  // Already unique by default
   db.comments.createIndex({post_id: 1})  // For post-based queries
   db.comments.createIndex({parent_comment_id: 1})  // For reply queries
   ```

---

## 🚀 Setup and Installation

### Prerequisites

1. **Python 3.7+** installed
2. **MongoDB** database (local or cloud)
3. **Facebook Developer Account** with:
   - App created
   - Access token generated
   - Group access permissions

### Step-by-Step Setup

#### Step 1: Clone/Download the Repository

```bash
cd "Lấy dữ liệu"
```

#### Step 2: Install Dependencies

```bash
pip install requests pymongo python-dotenv
```

Or create a `requirements.txt`:

```txt
requests>=2.31.0
pymongo>=4.6.0
python-dotenv>=1.0.0
```

Then install:

```bash
pip install -r requirements.txt
```

#### Step 3: Configure Environment Variables

**For post collection scripts** (`getpost.py`, `nckhgetposts.py`):

1. Create `.env` file in the folder:
   ```bash
   touch .env
   ```

2. Add configuration:
   ```env
   FB_ACCESS_TOKEN=EAAZA5WMoamSYBQ...
   FB_GROUP_ID=1170189375194877
   FB_GRAPH_VERSION=v24.0
   MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/
   MONGO_DB_NAME=chatbotNeu
   MONGO_COLLECTION=posts
   ```

**For comment collection scripts** (`getcomments.py`, `nckhgetcmt.py`):

1. Edit the script directly:
   ```python
   ACCESS_TOKEN = "your_token_here"
   GROUP_ID = "1170189375194877"
   MONGO_URI = "mongodb+srv://..."
   DB_NAME = "chatbotNeu"
   ```

#### Step 4: Verify MongoDB Connection

Test MongoDB connection:

```python
from pymongo import MongoClient

client = MongoClient("your_mongo_uri")
db = client["chatbotNeu"]
print(db.list_collection_names())  # Should show existing collections
```

#### Step 5: Verify Facebook API Access

Test API access:

```python
import requests

ACCESS_TOKEN = "your_token"
GROUP_ID = "1170189375194877"
url = f"https://graph.facebook.com/v24.0/{GROUP_ID}/feed?limit=1&access_token={ACCESS_TOKEN}"

response = requests.get(url)
print(response.json())
```

---

## 📖 Usage Guide

### Running Post Collection

#### Option 1: Using `getpost.py` (Recommended - uses .env)

```bash
python getpost.py
```

**Expected Output**:
```
Found 5 new posts

Saved post 1170189375194877_1174246348122513
Saved post 1170189375194877_1174252604788554
...

DONE.
```

#### Option 2: Using `nckhgetposts.py` (Alternative)

```bash
python nckhgetposts.py
```

**Behavior**:
- Fetches posts from group feed
- Stops at first existing post (incremental)
- Saves new posts to MongoDB
- Prints progress messages

### Running Comment Collection

#### Option 1: Using `getcomments.py`

```bash
python getcomments.py
```

**Expected Output**:
```
📌 Crawling comments for post 1170189375194877_1174246348122513
Reached old comment 1174291021451379 → stop
   ➜ Saved 3 new root comments

📌 Crawling comments for post 1170189375194877_1174252604788554
...

DONE. Incremental comment crawl finished.
```

#### Option 2: Using `nckhgetcmt.py`

```bash
python nckhgetcmt.py
```

**Behavior**:
- Reads all posts from MongoDB
- For each post, fetches new comments
- Fetches replies for each comment
- Stops at first existing comment (incremental)
- Saves to MongoDB

### Complete Workflow Example

```bash
# Step 1: Collect new posts
python getpost.py

# Step 2: Collect comments for all posts
python getcomments.py

# Step 3: (Optional) Export to CSV for backup
# Use MongoDB export tools or write custom export script

# Step 4: Process in RAG module (in ../RAG_chatbot/)
cd ../RAG_chatbot
python scripts/index_mongo.py
python scripts/embed_bge_m3.py
```

### Scheduling Regular Updates

For continuous data collection, schedule scripts to run periodically:

**Windows Task Scheduler**:
```powershell
# Create scheduled task to run daily
schtasks /create /tn "FacebookDataCollection" /tr "python C:\path\to\getpost.py" /sc daily /st 09:00
```

**Linux Cron**:
```bash
# Add to crontab (runs daily at 9 AM)
0 9 * * * cd /path/to/folder && python getpost.py >> logs/post_collection.log 2>&1
0 10 * * * cd /path/to/folder && python getcomments.py >> logs/comment_collection.log 2>&1
```

---

## 📊 Output Data Format

### MongoDB Document Structure

#### Posts Collection

```json
{
  "_id": "1170189375194877_1174246348122513",
  "group_id": "1170189375194877",
  "permalink_url": "https://www.facebook.com/groups/.../permalink/...",
  "author": {
    "id": "user_id",
    "name": "User Name"
  },
  "message": "Post content text...",
  "created_time": "2026-01-05T09:14:48+0000",
  "updated_time": "2026-01-05T13:37:00+0000",
  "full_picture": "https://...",
  "comments_count": 7,
  "shares_count": 0,
  "reactions": {
    "LIKE": 0,
    "LOVE": 0,
    "HAHA": 0,
    "WOW": 0,
    "SAD": 0,
    "ANGRY": 0
  },
  "fetched_at": "2026-01-09T07:47:28.815Z"
}
```

#### Comments Collection

```json
{
  "_id": "1174249041455577",
  "post_id": "1170189375194877_1174246348122513",
  "parent_comment_id": null,  // null for root comments
  "permalink_url": "https://www.facebook.com/groups/.../permalink/...",
  "message": "Comment text...",
  "like_count": 1,
  "reactions_count": 1,
  "created_time": "2026-01-05T09:20:23+0000",
  "fetched_at": "2026-01-05T11:15:10.737Z"
}
```

**Reply Structure** (nested comment):
```json
{
  "_id": "reply_comment_id",
  "post_id": "1170189375194877_1174246348122513",
  "parent_comment_id": "1174249041455577",  // Points to parent comment
  "message": "Reply text...",
  ...
}
```

### CSV Export Format

#### Posts CSV (`chatbotNeu.posts.csv`)

Headers:
```
_id,author,comments_count,created_time,fetched_at,full_picture,group_id,message,reactions.LIKE,reactions.LOVE,reactions.HAHA,reactions.WOW,reactions.SAD,reactions.ANGRY,shares_count,updated_time,permalink_url
```

#### Comments CSV (`chatbotNeu.comments.csv`)

Headers:
```
_id,created_time,fetched_at,like_count,message,parent_comment_id,permalink_url,post_id,reactions_count
```

#### Knowledge Base CSV (`chatbotNeu.knowledge_base.csv`)

Headers:
```
_id,type,text,source.post_id,source.permalink_url,created_time,fetched_at,embedding[0],embedding[1],...,embedding[1023]
```

- Contains normalized text from posts/comments
- Includes 1024-dimensional dense embeddings
- Generated by RAG module's embedding script

---

## ⚠️ Common Issues and Troubleshooting

### Issue 1: "Missing FB_ACCESS_TOKEN in .env"

**Error**:
```
❌ Missing FB_ACCESS_TOKEN in .env
```

**Solution**:
1. Create `.env` file in the script directory
2. Add `FB_ACCESS_TOKEN=your_token_here`
3. Ensure `.env` file is in the same directory as the script

### Issue 2: "Invalid OAuth Access Token"

**Error**:
```json
{
  "error": {
    "message": "Invalid OAuth access token.",
    "type": "OAuthException",
    "code": 190
  }
}
```

**Solutions**:
1. **Token Expired**: Generate a new access token from Facebook Developer Console
2. **Invalid Permissions**: Ensure token has `groups_access_member_info` permission
3. **Token Format**: Verify token is copied correctly (no extra spaces)

**How to Generate New Token**:
1. Go to [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Add required permissions
4. Generate token
5. Update `.env` or script

### Issue 3: "Rate Limit Exceeded"

**Error**:
```json
{
  "error": {
    "message": "Application request limit reached",
    "type": "OAuthException",
    "code": 4
  }
}
```

**Solutions**:
1. **Increase Delays**: Modify `time.sleep()` values in scripts
   ```python
   time.sleep(2)  # Increase from 1 to 2 seconds
   ```
2. **Reduce Batch Size**: Lower `limit` parameter in API calls
   ```python
   "limit": 5,  # Reduce from 10 to 5
   ```
3. **Wait and Retry**: Wait 1 hour and retry
4. **Use Different Token**: Rotate between multiple access tokens

### Issue 4: "Group Not Found" or "Insufficient Permissions"

**Error**:
```json
{
  "error": {
    "message": "Unsupported get request.",
    "type": "GraphMethodException",
    "code": 100
  }
}
```

**Solutions**:
1. **Verify Group ID**: Ensure GROUP_ID is correct
2. **Check Group Type**: Some group types may not be accessible via API
3. **Verify Permissions**: Token must have access to the group
4. **Group Privacy**: Private groups require admin approval

### Issue 5: MongoDB Connection Failed

**Error**:
```
pymongo.errors.ServerSelectionTimeoutError
```

**Solutions**:
1. **Check Connection String**: Verify MONGO_URI is correct
2. **Network Access**: Ensure MongoDB allows connections from your IP
3. **Credentials**: Verify username/password in connection string
4. **MongoDB Status**: Check if MongoDB service is running

**Test Connection**:
```python
from pymongo import MongoClient
try:
    client = MongoClient("your_uri", serverSelectionTimeoutMS=5000)
    client.server_info()  # Force connection
    print("✅ Connected successfully")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Issue 6: "No New Posts/Comments Found"

**Behavior**: Script runs but finds no new data

**Possible Causes**:
1. **Already Up-to-Date**: All posts/comments already in database
2. **Incremental Logic**: Script stops at first existing item
3. **API Ordering**: Posts may not be in expected order

**Solutions**:
1. **Check Database**: Verify what's already stored
   ```python
   from pymongo import MongoClient
   client = MongoClient("your_uri")
   db = client["chatbotNeu"]
   print(f"Posts: {db.posts.count_documents({})}")
   print(f"Comments: {db.comments.count_documents({})}")
   ```
2. **Force Full Scan**: Temporarily modify script to skip existence check
3. **Check API**: Verify API returns data
   ```python
   import requests
   url = f"https://graph.facebook.com/v24.0/{GROUP_ID}/feed?limit=5&access_token={TOKEN}"
   print(requests.get(url).json())
   ```

### Issue 7: Duplicate Data in Database

**Symptom**: Same posts/comments appear multiple times

**Causes**:
1. Script run multiple times without proper incremental logic
2. `_id` field not matching API response
3. Upsert operation failing

**Solutions**:
1. **Clean Database**: Remove duplicates
   ```python
   # Remove duplicate posts
   db.posts.create_index("_id", unique=True)
   # Remove duplicate comments
   db.comments.create_index("_id", unique=True)
   ```
2. **Verify Upsert**: Ensure `update_one` with `upsert=True` is used
3. **Check _id Format**: Verify `_id` matches API response `id` field

### Issue 8: Script Hangs or Takes Too Long

**Possible Causes**:
1. Large number of posts/comments
2. Network latency
3. Rate limiting causing retries

**Solutions**:
1. **Add Progress Logging**: Print progress every N items
2. **Reduce Batch Size**: Process fewer items per run
3. **Increase Timeouts**: Add timeout to requests
   ```python
   requests.get(url, params=params, timeout=30)
   ```
4. **Run Incrementally**: Run scripts more frequently with smaller batches

---

## 🔒 Security Considerations

### ⚠️ Critical Security Issues

#### 1. Hardcoded Credentials

**Problem**: `getcomments.py` and `nckhgetcmt.py` contain hardcoded access tokens and MongoDB credentials.

**Risk**: 
- Tokens exposed in version control
- Credentials visible to anyone with file access
- Cannot rotate credentials without code changes

**Recommendation**:
- **Migrate to `.env` file** (like `getpost.py`)
- **Never commit `.env` files** to version control
- Add `.env` to `.gitignore`
- Use environment variables in production

**Example Fix**:
```python
# Before (INSECURE)
ACCESS_TOKEN = "EAAZA5WMoamSYBQ..."

# After (SECURE)
import os
from dotenv import load_dotenv
load_dotenv()
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
```

#### 2. Access Token Management

**Best Practices**:
- Use **short-lived tokens** when possible
- Implement **token refresh** mechanism
- Store tokens in **secure vault** (AWS Secrets Manager, Azure Key Vault)
- **Rotate tokens** regularly
- **Monitor token usage** for anomalies

#### 3. MongoDB Security

**Recommendations**:
- Use **connection string authentication**
- Enable **IP whitelisting** in MongoDB Atlas
- Use **read-only user** for data collection scripts
- Enable **MongoDB encryption** at rest
- Use **VPN** or **private network** for database access

#### 4. API Key Protection

**Do**:
- Store credentials in environment variables
- Use `.env` files (excluded from git)
- Implement credential rotation
- Monitor API usage

**Don't**:
- Commit tokens to git
- Share tokens in chat/email
- Use production tokens in development
- Hardcode credentials in scripts

### Recommended `.gitignore` Entries

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Credentials
*.key
*.pem
secrets/

# Logs (may contain sensitive data)
*.log
logs/

# Database dumps
*.dump
*.backup
```

---

## 📝 Additional Notes

### API Rate Limits

Facebook Graph API has rate limits:
- **User-level**: ~200 calls per hour per user
- **App-level**: Varies by app type and usage
- **Recommendation**: Add exponential backoff for rate limit errors

### Data Retention

Consider implementing:
- **Data archival** for old posts/comments
- **TTL indexes** for automatic cleanup
- **Backup strategy** before deletion

### Monitoring

Recommended monitoring:
- **Script execution logs**
- **API call counts**
- **Database growth**
- **Error rates**
- **Data freshness** (last update timestamp)

### Future Enhancements

Potential improvements:
1. **Error recovery**: Resume from last successful item
2. **Parallel processing**: Process multiple posts concurrently
3. **Webhook integration**: Real-time updates instead of polling
4. **Data validation**: Verify data quality before storage
5. **Metrics dashboard**: Visualize collection statistics

---

## 📚 References

- [Facebook Graph API Documentation](https://developers.facebook.com/docs/graph-api)
- [MongoDB Python Driver Documentation](https://pymongo.readthedocs.io/)
- [Python Requests Library](https://requests.readthedocs.io/)
- [RAG Chatbot Module](../RAG_chatbot/README.md)

---

## 📧 Support

For issues or questions:
1. Check [Common Issues](#common-issues-and-troubleshooting) section
2. Review Facebook Graph API documentation
3. Check MongoDB connection and permissions
4. Verify environment variables are set correctly

---

**Last Updated**: 2026-01-09  
**Version**: 1.0.0  
**Maintainer**: Data Collection Team


