#!/usr/bin/env python3
"""
Test semantic search API functionality
"""

import requests
import json
import time

def test_semantic_search():
    """Test semantic search API"""
    base_url = "http://localhost:8000"
    
    # Wait for server to start
    time.sleep(3)
    
    # Test root endpoint
    print("Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Root: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Endpoints: {data.get('endpoints', {})}")
    except Exception as e:
        print(f"Root error: {e}")
    
    # Test search stats
    print("\nTesting search stats...")
    try:
        response = requests.get(f"{base_url}/api/search/stats")
        print(f"Stats: {response.status_code}")
        if response.status_code == 200:
            print(f"Stats data: {response.json()}")
        else:
            print(f"Stats error: {response.text}")
    except Exception as e:
        print(f"Stats error: {e}")
    
    # Test semantic search
    print("\nTesting semantic search...")
    try:
        payload = {"query": "meaning of life", "top_k": 3}
        response = requests.post(f"{base_url}/api/search/semantic", json=payload)
        print(f"Search: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Results: {len(data.get('results', []))} found")
            for i, result in enumerate(data.get('results', [])[:2]):
                print(f"  {i+1}. {result.get('text', '')[:100]}...")
        else:
            print(f"Search error: {response.text}")
    except Exception as e:
        print(f"Search error: {e}")

if __name__ == "__main__":
    test_semantic_search()
