"""
Script để test Flask API endpoints.
Chạy script này để kiểm tra xem API có hoạt động đúng không.
"""

import requests
import json
import sys

API_BASE_URL = "http://localhost:5000"


def test_health():
    """Test health check endpoint."""
    print("=" * 60)
    print("1. Testing /api/health endpoint...")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        if response.status_code == 200:
            print("✅ Health check PASSED")
            return True
        else:
            print("❌ Health check FAILED")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: API server không chạy hoặc không thể kết nối")
        print("   Hãy chạy: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_root():
    """Test root endpoint."""
    print("\n" + "=" * 60)
    print("2. Testing / (root) endpoint...")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        if response.status_code == 200:
            print("✅ Root endpoint PASSED")
            return True
        else:
            print("❌ Root endpoint FAILED")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat():
    """Test chat endpoint."""
    print("\n" + "=" * 60)
    print("3. Testing /api/chat endpoint...")
    print("=" * 60)
    try:
        test_question = "thầy Phùng Ngọc Tùng dạy cái gì"
        print(f"Question: {test_question}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={"question": test_question},
            headers={"Content-Type": "application/json"},
            timeout=30  # Chat có thể mất thời gian
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Chat endpoint PASSED")
                return True
            else:
                print(f"⚠️  Chat endpoint returned error: {data.get('error')}")
                return False
        else:
            print(f"❌ Chat endpoint FAILED with status {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Timeout: Request mất quá nhiều thời gian (>30s)")
        print("   Có thể do model đang load hoặc xử lý chậm")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_404():
    """Test 404 error handling."""
    print("\n" + "=" * 60)
    print("4. Testing 404 error handling...")
    print("=" * 60)
    try:
        response = requests.get(f"{API_BASE_URL}/api/nonexistent", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        if response.status_code == 404:
            print("✅ 404 error handling PASSED")
            return True
        else:
            print("❌ 404 error handling FAILED")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print(" RAG CHATBOT API TEST")
    print("=" * 60 + "\n")
    
    print(f"Testing API at: {API_BASE_URL}\n")
    
    results = []
    
    # Test health check
    results.append(("Health Check", test_health()))
    
    # Test root
    results.append(("Root Endpoint", test_root()))
    
    # Test 404
    results.append(("404 Error Handling", test_404()))
    
    # Test chat (only if health check passed)
    if results[0][1]:  # If health check passed
        results.append(("Chat Endpoint", test_chat()))
    else:
        print("\n⚠️  Skipping chat test because health check failed")
        results.append(("Chat Endpoint", False))
    
    # Summary
    print("\n" + "=" * 60)
    print(" TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)









