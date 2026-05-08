import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"


def test_health():
    print("Testing /api/health...")
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200, "Health check failed!"
    data = response.json()
    assert data["status"] == "healthy", "Unexpected health status"
    print("Health check OK:", data)


def test_history():
    print("Testing /api/history...")
    params = {"limit": 5, "offset": 0}
    response = requests.get(f"{BASE_URL}/api/history", params=params)
    assert response.status_code == 200, "History endpoint failed!"
    data = response.json()
    assert "history" in data, "Missing 'history' in response"
    print(f"Retrieved {len(data['history'])} entries from history.")


def test_analytics():
    print("Testing /api/analytics...")
    response = requests.get(f"{BASE_URL}/api/analytics")
    assert response.status_code == 200, "Analytics endpoint failed!"
    data = response.json()
    assert "total_requests" in data, "Missing 'total_requests' in analytics"
    print("Analytics data:", json.dumps(data, indent=2))

def test_cache_basic():
    """Test basic cache functionality"""
    print("\nTesting cache functionality...")
    
    # Clear cache first
    requests.post(f"{BASE_URL}/api/cache/clear")
    
    # Test calculator cache
    print("Testing calculator cache...")
    
    # First request (should be cache miss)
    start_time = time.time()
    response1 = requests.post(f"{BASE_URL}/api/calculate", json={
        "operation_type": "calculator",
        "input_value": "2 + 2"
    })
    time1 = time.time() - start_time
    
    assert response1.status_code == 200, "First calculator request failed!"
    data1 = response1.json()
    assert data1["cached"] == False, "First request should not be cached!"
    print(f"First request: {data1['result']} (Time: {time1:.4f}s, Cached: {data1['cached']})")
    
    # Second identical request (should be cache hit)
    start_time = time.time()
    response2 = requests.post(f"{BASE_URL}/api/calculate", json={
        "operation_type": "calculator",
        "input_value": "2 + 2"
    })
    time2 = time.time() - start_time
    
    assert response2.status_code == 200, "Second calculator request failed!"
    data2 = response2.json()
    assert data2["cached"] == True, "Second request should be cached!"
    print(f"Second request: {data2['result']} (Time: {time2:.4f}s, Cached: {data2['cached']})")
    
    if time2 < time1:
        print(f"Cache speedup: {time1/time2:.2f}x faster!")
    
    # Test fibonacci cache
    print("\nTesting fibonacci cache...")
    
    response3 = requests.post(f"{BASE_URL}/api/calculate", json={
        "operation_type": "fibonacci",
        "input_value": "10"
    })
    
    assert response3.status_code == 200, "Fibonacci request failed!"
    data3 = response3.json()
    assert data3["cached"] == False, "First fibonacci should not be cached!"
    print(f"Fibonacci(10) = {data3['result']} (Cached: {data3['cached']})")
    
    # Second identical fibonacci request
    response4 = requests.post(f"{BASE_URL}/api/calculate", json={
        "operation_type": "fibonacci",
        "input_value": "10"
    })
    
    assert response4.status_code == 200, "Second fibonacci request failed!"
    data4 = response4.json()
    assert data4["cached"] == True, "Second fibonacci should be cached!"
    print(f"Fibonacci(10) = {data4['result']} (Cached: {data4['cached']})")


def test_cache_stats():
    """Test cache statistics"""
    print("\nTesting cache statistics...")
    
    response = requests.get(f"{BASE_URL}/api/cache/stats")
    assert response.status_code == 200, "Cache stats failed!"
    data = response.json()
    
    assert "cache_stats" in data, "Missing cache_stats in response"
    stats = data["cache_stats"]
    
    print("Cache Statistics:")
    print(f"  Hits: {stats['hit_count']}")
    print(f"  Misses: {stats['miss_count']}")
    print(f"  Hit Rate: {stats['hit_rate']}%")
    print(f"  Cache Sizes: {stats['cache_sizes']}")


def test_specific_endpoints():
    """Test operation-specific endpoints"""
    print("\nTesting specific endpoints...")
    
    # Test calculator endpoint
    response = requests.post(f"{BASE_URL}/api/calculator", json={
        "expression": "sqrt(16)"
    })
    assert response.status_code == 200, "Calculator endpoint failed!"
    data = response.json()
    print(f"Calculator endpoint: sqrt(16) = {data['result']}")
    
    # Test fibonacci endpoint
    response = requests.post(f"{BASE_URL}/api/fibonacci", json={
        "n": 8
    })
    assert response.status_code == 200, "Fibonacci endpoint failed!"
    data = response.json()
    print(f"Fibonacci endpoint: F(8) = {data['result']}")
    
    # Test factorial endpoint
    response = requests.post(f"{BASE_URL}/api/factorial", json={
        "n": 5
    })
    assert response.status_code == 200, "Factorial endpoint failed!"
    data = response.json()
    print(f"Factorial endpoint: 5! = {data['result']}")

if __name__ == "__main__":
    try:
        test_health()
        test_history()
        test_analytics()
        
        test_cache_basic()
        test_cache_stats()
        test_specific_endpoints()
        
        print("\nAll tests passed successfully!")
    except AssertionError as ae:
        print("\nTest failed:", ae)
    except Exception as e:
        print("\nUnexpected error occurred:", e)
