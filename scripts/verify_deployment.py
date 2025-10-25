#!/usr/bin/env python3
"""
Copilot addition: deployment prep - Deployment verification script
Confirms API health and connectivity
"""

import os
import sys
import requests
from typing import Dict, Any

def check_api_health(base_url: str) -> Dict[str, Any]:
    """Check API system health"""
    try:
        response = requests.get(f"{base_url}/api/verify/system", timeout=10)
        
        if response.ok:
            data = response.json()
            return {
                "status": "✅ Online",
                "code": response.status_code,
                "data": data
            }
        else:
            return {
                "status": "❌ Offline",
                "code": response.status_code,
                "error": response.text
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "❌ Connection Failed",
            "code": None,
            "error": "Cannot connect to API server"
        }
    except requests.exceptions.Timeout:
        return {
            "status": "❌ Timeout",
            "code": None,
            "error": "API request timed out"
        }
    except Exception as e:
        return {
            "status": "❌ Error",
            "code": None,
            "error": str(e)
        }

def main():
    # Get API base URL from environment or use default
    base_url = os.getenv("VITE_API_BASE", "http://localhost:8000")
    
    print(f"\n{'='*60}")
    print(f"🔍 TikTalk API Deployment Verification")
    print(f"{'='*60}\n")
    print(f"Testing API at: {base_url}")
    print(f"-" * 60)
    
    # Check system health
    result = check_api_health(base_url)
    
    print(f"\nStatus: {result['status']}")
    print(f"HTTP Code: {result['code']}")
    
    if result['code'] == 200 and 'data' in result:
        print(f"\n✅ API is healthy and responding")
        print(f"\nSystem Details:")
        for key, value in result['data'].items():
            print(f"  - {key}: {value}")
        print(f"\n{'='*60}\n")
        return 0
    else:
        print(f"\n❌ API verification failed")
        if 'error' in result:
            print(f"Error: {result['error']}")
        print(f"\n{'='*60}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
