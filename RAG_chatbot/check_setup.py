"""
Script kiểm tra setup hệ thống RAG Chatbot.
Chạy script này để xác nhận mọi thứ đã sẵn sàng trước khi chạy chatbot.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Kiểm tra phiên bản Python."""
    print("=" * 60)
    print("1. KIỂM TRA PYTHON VERSION")
    print("=" * 60)
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Cần Python >= 3.8")
        return False


def check_dependencies():
    """Kiểm tra các thư viện đã được cài đặt."""
    print("\n" + "=" * 60)
    print("2. KIỂM TRA DEPENDENCIES")
    print("=" * 60)
    
    required_packages = {
        "torch": "PyTorch",
        "transformers": "Transformers",
        "FlagEmbedding": "FlagEmbedding",
        "pymongo": "PyMongo",
        "dotenv": "python-dotenv",
        "numpy": "NumPy",
        "google.generativeai": "Google Generative AI"
    }
    
    missing = []
    for package, name in required_packages.items():
        try:
            if package == "dotenv":
                __import__("dotenv")
            elif package == "google.generativeai":
                __import__("google.generativeai")
            else:
                __import__(package)
            print(f"✅ {name} - OK")
        except ImportError:
            print(f"❌ {name} - CHƯA CÀI ĐẶT")
            missing.append(name)
    
    if missing:
        print(f"\n⚠️  Thiếu các packages: {', '.join(missing)}")
        print("   Chạy: pip install -r requirements.txt")
        return False
    return True


def check_gemini_key():
    """Kiểm tra Gemini API key."""
    print("\n" + "=" * 60)
    print("3. KIỂM TRA GEMINI API KEY")
    print("=" * 60)
    
    env_files = ["gemini.env", ".env"]
    api_key = None
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                print(f"✅ Tìm thấy API key trong {env_file}")
                print(f"   Key (3 ký tự đầu): {api_key[:3]}...")
                return True
    
    print("❌ Không tìm thấy GEMINI_API_KEY")
    print("   Tạo file 'gemini.env' với nội dung:")
    print("   GEMINI_API_KEY=your_api_key_here")
    return False


def check_mongodb():
    """Kiểm tra kết nối MongoDB và dữ liệu."""
    print("\n" + "=" * 60)
    print("4. KIỂM TRA MONGODB & QDRANT")
    print("=" * 60)
    
    try:
        from src.utils.config import get_mongo_client, MONGO_DB_SOURCE, get_qdrant_client, QDRANT_COLLECTION_NAME
        
        # Kiểm tra MongoDB (dữ liệu nguồn)
        client = get_mongo_client()
        client.admin.command('ping')
        print("✅ Kết nối MongoDB thành công")
        
        # Đọc posts và comments từ database Postandcmt (source)
        source_db = client[MONGO_DB_SOURCE]
        posts_count = source_db.posts.count_documents({})
        comments_count = source_db.comments.count_documents({})
        
        print(f"   MongoDB - Database '{MONGO_DB_SOURCE}' (source):")
        print(f"     - Posts: {posts_count}")
        print(f"     - Comments: {comments_count}")
        
        if posts_count == 0 and comments_count == 0:
            print("⚠️  Chưa có dữ liệu trong MongoDB (posts và comments)")
            return False
        
        # Kiểm tra Qdrant (knowledge base)
        qdrant_client = get_qdrant_client()
        
        try:
            collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
            total_points = collection_info.points_count
            print(f"\n✅ Kết nối Qdrant thành công")
            print(f"   Qdrant - Collection '{QDRANT_COLLECTION_NAME}':")
            print(f"     - Total points: {total_points}")
            
            # Đếm số points có embedding thực (không phải zero vector)
            points_sample, _ = qdrant_client.scroll(
                collection_name=QDRANT_COLLECTION_NAME,
                limit=100,
                with_payload=True,
                with_vectors=True,
            )
            
            if points_sample:
                embedded_count = sum(1 for p in points_sample if p.vector and sum(p.vector) != 0)
                estimated_embedded = int((embedded_count / len(points_sample)) * total_points)
                print(f"     - Points có embeddings: ~{estimated_embedded}/{total_points} (estimated)")
                
                if total_points == 0:
                    print("⚠️  Chưa có knowledge_base trong Qdrant. Chạy: python scripts/index_mongo.py")
                    return False
                
                if embedded_count == 0:
                    print("⚠️  Chưa có embeddings. Chạy: python scripts/embed_bge_m3.py")
                    return False
                
                if embedded_count < len(points_sample):
                    print(f"⚠️  Một số documents chưa có embeddings")
                    print("   Chạy lại: python scripts/embed_bge_m3.py")
            
        except Exception as e:
            print(f"❌ Lỗi kết nối Qdrant: {e}")
            print(f"   Kiểm tra QDRANT_URL và QDRANT_KEY trong .env hoặc src/utils/config.py")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False


def check_model():
    """Kiểm tra model BGE-M3 (không bắt buộc, chỉ cảnh báo)."""
    print("\n" + "=" * 60)
    print("5. KIỂM TRA MODEL BGE-M3")
    print("=" * 60)
    
    try:
        from FlagEmbedding import BGEM3FlagModel
        print("✅ FlagEmbedding library đã được cài đặt")
        print("ℹ️  Model sẽ tự động download khi chạy lần đầu (~2GB)")
        return True
    except ImportError:
        print("❌ FlagEmbedding chưa được cài đặt")
        print("   Chạy: pip install FlagEmbedding")
        return False


def main():
    """Chạy tất cả các kiểm tra."""
    print("\n" + "=" * 60)
    print(" KIỂM TRA SETUP RAG CHATBOT")
    print("=" * 60 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Gemini API Key", check_gemini_key),
        ("MongoDB", check_mongodb),
        ("Model Library", check_model),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Lỗi khi kiểm tra {name}: {e}")
            results.append((name, False))
    
    # Tổng kết
    print("\n" + "=" * 60)
    print(" TỔNG KẾT")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TẤT CẢ ĐÃ SẴN SÀNG! Bạn có thể chạy: python chat_cli.py")
    else:
        print("❌ CÓ MỘT SỐ VẤN ĐỀ. Vui lòng kiểm tra và sửa các lỗi trên.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

