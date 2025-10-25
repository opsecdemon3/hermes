#!/usr/bin/env python3
"""
Comprehensive Test Suite for TikTok Transcription Pipeline
Tests all features systematically and provides detailed reporting
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple


class FeatureTester:
    """Test all features of the TikTok transcription pipeline"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.results = {
            "dependencies": False,
            "single_ingestion": False,
            "idempotency": False,
            "batch_processing": False,
            "data_verification": False,
            "topic_extraction": False,
            "topic_listing": False,
            "api_server": False,
            "error_handling": False
        }
        self.test_account = "kwrt_"
        self.test_videos = 3
        
    def run_command(self, cmd: List[str], timeout: int = 300) -> Tuple[bool, str, str]:
        """Run a command and return success, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=self.base_dir
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def test_dependencies(self) -> bool:
        """Test 1: Dependencies"""
        print("🧪 Testing Dependencies...")
        success, stdout, stderr = self.run_command(["python3", "test_dependencies.py"])
        
        if success and "All dependencies are working!" in stdout:
            print("✅ Dependencies: PASSED")
            self.results["dependencies"] = True
            return True
        else:
            print("❌ Dependencies: FAILED")
            print(f"Error: {stderr}")
            return False
    
    def test_single_ingestion(self) -> bool:
        """Test 2: Single Account Ingestion"""
        print("🧪 Testing Single Account Ingestion...")
        
        # Test with tiny model for speed
        cmd = [
            "python3", "scripts/ingest_account.py",
            "--user", self.test_account,
            "--max-videos", str(self.test_videos),
            "--model-size", "tiny",
            "-v"
        ]
        
        success, stdout, stderr = self.run_command(cmd, timeout=600)
        
        if success and ("TRANSCRIBED and SAVED" in stdout or "already processed" in stdout):
            print("✅ Single Ingestion: PASSED")
            self.results["single_ingestion"] = True
            return True
        else:
            print("❌ Single Ingestion: FAILED")
            print(f"Error: {stderr}")
            return False
    
    def test_idempotency(self) -> bool:
        """Test 3: Idempotency (run same command twice)"""
        print("🧪 Testing Idempotency...")
        
        cmd = [
            "python3", "scripts/ingest_account.py",
            "--user", self.test_account,
            "--max-videos", str(self.test_videos),
            "--model-size", "tiny"
        ]
        
        success, stdout, stderr = self.run_command(cmd, timeout=300)
        
        if success and ("already processed" in stdout and "SKIPPED" in stdout):
            print("✅ Idempotency: PASSED")
            self.results["idempotency"] = True
            return True
        else:
            print("❌ Idempotency: FAILED")
            print(f"Error: {stderr}")
            return False
    
    def test_batch_processing(self) -> bool:
        """Test 4: Batch Processing"""
        print("🧪 Testing Batch Processing...")
        
        cmd = [
            "python3", "scripts/batch_ingest.py",
            "--users", "kwrt_", "matrix.v5",
            "--max-videos", str(self.test_videos)
        ]
        
        success, stdout, stderr = self.run_command(cmd, timeout=900)
        
        if success and "BATCH INGESTION SUMMARY" in stdout:
            print("✅ Batch Processing: PASSED")
            self.results["batch_processing"] = True
            return True
        else:
            print("❌ Batch Processing: FAILED")
            print(f"Error: {stderr}")
            return False
    
    def test_data_verification(self) -> bool:
        """Test 5: Data Integrity Verification"""
        print("🧪 Testing Data Verification...")
        
        cmd = ["python3", "scripts/verify_ingestion.py", "--account", self.test_account]
        success, stdout, stderr = self.run_command(cmd)
        
        if success and "Perfect data integrity!" in stdout:
            print("✅ Data Verification: PASSED")
            self.results["data_verification"] = True
            return True
        else:
            print("❌ Data Verification: FAILED")
            print(f"Error: {stderr}")
            return False
    
    def test_topic_extraction(self) -> bool:
        """Test 6: Topic Extraction"""
        print("🧪 Testing Topic Extraction...")
        
        cmd = ["python3", "scripts/extract_topics.py", "--user", self.test_account, "-v"]
        success, stdout, stderr = self.run_command(cmd, timeout=300)
        
        if success and "Tag extraction & category classification complete!" in stdout:
            print("✅ Topic Extraction: PASSED")
            self.results["topic_extraction"] = True
            return True
        else:
            print("❌ Topic Extraction: FAILED")
            print(f"Error: {stderr}")
            return False
    
    def test_topic_listing(self) -> bool:
        """Test 7: Topic Listing"""
        print("🧪 Testing Topic Listing...")
        
        # Test category listing
        cmd = ["python3", "scripts/list_topics.py", "--user", self.test_account, "--category"]
        success, stdout, stderr = self.run_command(cmd)
        
        if success and "Category:" in stdout and "Confidence:" in stdout:
            print("✅ Topic Listing: PASSED")
            self.results["topic_listing"] = True
            return True
        else:
            print("❌ Topic Listing: FAILED")
            print(f"Error: {stderr}")
            return False
    
    def test_api_server(self) -> bool:
        """Test 8: API Server"""
        print("🧪 Testing API Server...")
        
        # Start server in background
        server_cmd = ["python3", "api_server.py", "--host", "127.0.0.1", "--port", "8001"]
        server_process = subprocess.Popen(server_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            # Wait for server to start
            time.sleep(3)
            
            # Test API endpoints
            import requests
            
            # Test root endpoint
            response = requests.get("http://127.0.0.1:8001/", timeout=5)
            if response.status_code == 200:
                # Test accounts endpoint
                response = requests.get("http://127.0.0.1:8001/api/accounts", timeout=5)
                if response.status_code == 200:
                    # Test category endpoint
                    response = requests.get(f"http://127.0.0.1:8001/api/accounts/{self.test_account}/category", timeout=5)
                    if response.status_code == 200:
                        print("✅ API Server: PASSED")
                        self.results["api_server"] = True
                        return True
            
            print("❌ API Server: FAILED")
            return False
            
        except Exception as e:
            print(f"❌ API Server: FAILED - {e}")
            return False
        finally:
            # Clean up server
            server_process.terminate()
            server_process.wait()
    
    def test_error_handling(self) -> bool:
        """Test 9: Error Handling"""
        print("🧪 Testing Error Handling...")
        
        # Test with non-existent account
        cmd = [
            "python3", "scripts/ingest_account.py",
            "--user", "nonexistent_account_xyz",
            "--max-videos", "1"
        ]
        
        success, stdout, stderr = self.run_command(cmd, timeout=60)
        
        # Should fail gracefully
        if not success and "Unable to extract" in stderr:
            print("✅ Error Handling: PASSED")
            self.results["error_handling"] = True
            return True
        else:
            print("❌ Error Handling: FAILED")
            print(f"Unexpected success or different error: {stderr}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print("=" * 80)
        print("🚀 COMPREHENSIVE FEATURE TESTING")
        print("=" * 80)
        print()
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_dependencies,
            self.test_single_ingestion,
            self.test_idempotency,
            self.test_batch_processing,
            self.test_data_verification,
            self.test_topic_extraction,
            self.test_topic_listing,
            self.test_api_server,
            self.test_error_handling
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
            print()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate results
        passed = sum(1 for result in self.results.values() if result)
        total = len(self.results)
        
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Tests passed: {passed}/{total}")
        print(f"Duration: {duration:.1f}s")
        print()
        
        for feature, result in self.results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {feature.replace('_', ' ').title()}: {status}")
        
        print()
        if passed == total:
            print("🎉 ALL TESTS PASSED! The system is fully functional.")
        else:
            print(f"⚠️  {total - passed} tests failed. Check the output above for details.")
        
        return {
            "passed": passed,
            "total": total,
            "duration": duration,
            "results": self.results
        }


def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = "."
    
    tester = FeatureTester(base_dir)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["passed"] == results["total"] else 1)


if __name__ == "__main__":
    main()
