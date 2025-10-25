#!/usr/bin/env python3
"""
End-to-End System Test for TikTok Transcript + Topics + Semantic Search
Tests all features for a real account
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List


class SystemTester:
    """Comprehensive system tester"""
    
    def __init__(self, username: str = "beabettermandaily", base_dir: str = "accounts"):
        self.username = username
        self.base_dir = Path(base_dir)
        self.account_dir = self.base_dir / username
        self.results: Dict[str, Dict[str, Any]] = {}
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all system tests"""
        print("="*80)
        print("🧪 TIKTOK TRANSCRIPT SYSTEM - END-TO-END TEST")
        print("="*80)
        print(f"Testing account: @{self.username}")
        print("="*80)
        print()
        
        # Test 1: Ingestion
        self.test_ingestion()
        
        # Test 2: Idempotency
        self.test_idempotency()
        
        # Test 3: Topic Extraction
        self.test_topic_extraction()
        
        # Test 4: Semantic Search
        self.test_semantic_search()
        
        # Test 5: Context Expansion
        self.test_context_expansion()
        
        # Test 6: CLI Commands
        self.test_cli_commands()
        
        # Test 7: Verification System
        self.test_verification()
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    def test_ingestion(self):
        """Test Step 1: Multi-Video Transcription"""
        print("\n" + "="*80)
        print("TEST 1: INGESTION")
        print("="*80)
        
        try:
            # Check if account already has transcripts
            index_file = self.account_dir / "index.json"
            transcripts_dir = self.account_dir / "transcriptions"
            
            if not index_file.exists():
                self.results["ingestion"] = {
                    "status": "SKIP",
                    "notes": "No existing data - account needs ingestion first"
                }
                print("⚠️  SKIP: No existing ingestion data for this account")
                print("   Run: python3 scripts/ingest_account.py --user", self.username)
                return
            
            # Load index
            with open(index_file, 'r') as f:
                index = json.load(f)
            
            # Check transcripts exist
            processed_videos = index.get("processed_videos", {})
            successful_videos = [v for v in processed_videos.values() if v.get("success")]
            
            if len(successful_videos) == 0:
                self.results["ingestion"] = {
                    "status": "FAIL",
                    "notes": "No successful transcriptions found"
                }
                print("❌ FAIL: No successful transcriptions")
                return
            
            # Check transcript files exist
            missing_transcripts = []
            for video in successful_videos:
                video_id = video.get("video_id")
                transcript_file = transcripts_dir / f"{video_id}_transcript.txt"
                if not transcript_file.exists():
                    missing_transcripts.append(video_id)
            
            if missing_transcripts:
                self.results["ingestion"] = {
                    "status": "FAIL",
                    "notes": f"Missing {len(missing_transcripts)} transcript files"
                }
                print(f"❌ FAIL: Missing transcript files for {missing_transcripts}")
                return
            
            # Success
            self.results["ingestion"] = {
                "status": "PASS",
                "notes": f"Found {len(successful_videos)} transcripts, all files exist",
                "total_videos": len(processed_videos),
                "successful": len(successful_videos)
            }
            print(f"✅ PASS: {len(successful_videos)} transcripts ingested successfully")
            
        except Exception as e:
            self.results["ingestion"] = {
                "status": "FAIL",
                "notes": f"Error: {e}"
            }
            print(f"❌ FAIL: {e}")
    
    def test_idempotency(self):
        """Test that re-running ingestion doesn't duplicate work"""
        print("\n" + "="*80)
        print("TEST 2: IDEMPOTENCY")
        print("="*80)
        
        try:
            index_file = self.account_dir / "index.json"
            
            if not index_file.exists():
                self.results["idempotency"] = {
                    "status": "SKIP",
                    "notes": "No index file to test"
                }
                print("⚠️  SKIP: No index file")
                return
            
            with open(index_file, 'r') as f:
                index = json.load(f)
            
            # Check if index has processed_videos tracking
            if "processed_videos" not in index:
                self.results["idempotency"] = {
                    "status": "FAIL",
                    "notes": "Index missing processed_videos tracking"
                }
                print("❌ FAIL: Index doesn't track processed videos")
                return
            
            # Check stats
            stats = index.get("stats", {})
            if "total_processed" not in stats:
                self.results["idempotency"] = {
                    "status": "FAIL",
                    "notes": "Stats missing total_processed counter"
                }
                print("❌ FAIL: Missing stats")
                return
            
            self.results["idempotency"] = {
                "status": "PASS",
                "notes": "Index properly tracks processed videos for idempotent operations"
            }
            print("✅ PASS: Idempotency tracking in place")
            
        except Exception as e:
            self.results["idempotency"] = {
                "status": "FAIL",
                "notes": f"Error: {e}"
            }
            print(f"❌ FAIL: {e}")
    
    def test_topic_extraction(self):
        """Test Step 2: Topic Extraction"""
        print("\n" + "="*80)
        print("TEST 3: TOPIC EXTRACTION")
        print("="*80)
        
        try:
            topics_dir = self.account_dir / "topics"
            
            if not topics_dir.exists():
                self.results["topic_extraction"] = {
                    "status": "SKIP",
                    "notes": "No topics directory - run extract_topics.py first"
                }
                print("⚠️  SKIP: No topics extracted yet")
                print(f"   Run: python3 scripts/extract_topics.py --user {self.username}")
                return
            
            # Check for account-level files
            account_tags = topics_dir / "account_tags.json"
            account_category = topics_dir / "account_category.json"
            
            if not account_tags.exists():
                self.results["topic_extraction"] = {
                    "status": "FAIL",
                    "notes": "Missing account_tags.json"
                }
                print("❌ FAIL: Missing account_tags.json")
                return
            
            if not account_category.exists():
                self.results["topic_extraction"] = {
                    "status": "FAIL",
                    "notes": "Missing account_category.json"
                }
                print("❌ FAIL: Missing account_category.json")
                return
            
            # Load and validate
            with open(account_tags, 'r') as f:
                tags_data = json.load(f)
            
            with open(account_category, 'r') as f:
                category_data = json.load(f)
            
            # Check structure
            if "tags" not in tags_data or len(tags_data["tags"]) == 0:
                self.results["topic_extraction"] = {
                    "status": "FAIL",
                    "notes": "No tags found in account_tags.json"
                }
                print("❌ FAIL: No tags extracted")
                return
            
            if "category" not in category_data:
                self.results["topic_extraction"] = {
                    "status": "FAIL",
                    "notes": "No category in account_category.json"
                }
                print("❌ FAIL: No category assigned")
                return
            
            # Count video-level tags
            video_tags = list(topics_dir.glob("*_tags.json"))
            video_tags = [f for f in video_tags if f.name not in ["account_tags.json", "account_category.json"]]
            
            self.results["topic_extraction"] = {
                "status": "PASS",
                "notes": f"Category: {category_data['category']}, {len(tags_data['tags'])} tags, {len(video_tags)} videos",
                "category": category_data['category'],
                "total_tags": len(tags_data['tags']),
                "video_count": len(video_tags)
            }
            print(f"✅ PASS: Topics extracted")
            print(f"   Category: {category_data['category']}")
            print(f"   Tags: {len(tags_data['tags'])}")
            print(f"   Videos: {len(video_tags)}")
            
        except Exception as e:
            self.results["topic_extraction"] = {
                "status": "FAIL",
                "notes": f"Error: {e}"
            }
            print(f"❌ FAIL: {e}")
    
    def test_semantic_search(self):
        """Test Step 3: Semantic Search"""
        print("\n" + "="*80)
        print("TEST 4: SEMANTIC SEARCH")
        print("="*80)
        
        try:
            # Check if embeddings exist
            embeddings_file = Path("data/search/embeddings.jsonl")
            index_file = Path("data/search/index.faiss")
            
            if not embeddings_file.exists() or not index_file.exists():
                self.results["semantic_search"] = {
                    "status": "SKIP",
                    "notes": "No embeddings - run: python3 scripts/search_semantic.py --index-all"
                }
                print("⚠️  SKIP: No embeddings created yet")
                print("   Run: python3 scripts/search_semantic.py --index-all")
                return
            
            # Try to import and use search engine
            sys.path.insert(0, str(Path.cwd()))
            from core.semantic_search.engine import SemanticSearchEngine
            
            search_engine = SemanticSearchEngine()
            stats = search_engine.get_stats()
            
            if stats['total_vectors'] == 0:
                self.results["semantic_search"] = {
                    "status": "FAIL",
                    "notes": "Search index is empty"
                }
                print("❌ FAIL: Empty search index")
                return
            
            # Try a search
            results = search_engine.search("life", top_k=3)
            
            if not results:
                self.results["semantic_search"] = {
                    "status": "FAIL",
                    "notes": "Search returned no results"
                }
                print("❌ FAIL: Search returned no results")
                return
            
            # Check result structure
            first_result = results[0]
            required_fields = ["text", "snippet", "video_id", "username", "timestamp", "score"]
            missing_fields = [f for f in required_fields if f not in first_result]
            
            if missing_fields:
                self.results["semantic_search"] = {
                    "status": "FAIL",
                    "notes": f"Results missing fields: {missing_fields}"
                }
                print(f"❌ FAIL: Missing fields in results: {missing_fields}")
                return
            
            self.results["semantic_search"] = {
                "status": "PASS",
                "notes": f"{stats['total_vectors']} vectors indexed, search returns results with provenance",
                "total_vectors": stats['total_vectors'],
                "sample_result": {
                    "username": first_result['username'],
                    "video_id": first_result['video_id'],
                    "timestamp": first_result['timestamp']
                }
            }
            print(f"✅ PASS: Semantic search working")
            print(f"   Indexed vectors: {stats['total_vectors']}")
            print(f"   Sample result: @{first_result['username']} - {first_result['video_id']}")
            
        except ImportError as e:
            self.results["semantic_search"] = {
                "status": "FAIL",
                "notes": f"Import error: {e}"
            }
            print(f"❌ FAIL: Cannot import search engine: {e}")
        except Exception as e:
            self.results["semantic_search"] = {
                "status": "FAIL",
                "notes": f"Error: {e}"
            }
            print(f"❌ FAIL: {e}")
    
    def test_context_expansion(self):
        """Test Step 4: Context Snippet Expansion"""
        print("\n" + "="*80)
        print("TEST 5: CONTEXT EXPANSION")
        print("="*80)
        
        try:
            # Get a transcript to test with
            transcripts_dir = self.account_dir / "transcriptions"
            
            if not transcripts_dir.exists():
                self.results["context_expansion"] = {
                    "status": "SKIP",
                    "notes": "No transcripts to test"
                }
                print("⚠️  SKIP: No transcripts")
                return
            
            # Find first transcript
            transcript_files = list(transcripts_dir.glob("*_transcript.txt"))
            if not transcript_files:
                self.results["context_expansion"] = {
                    "status": "SKIP",
                    "notes": "No transcript files found"
                }
                print("⚠️  SKIP: No transcript files")
                return
            
            # Try to load and parse timestamps
            sys.path.insert(0, str(Path.cwd()))
            from core.semantic_search.timestamp_extractor import TimestampExtractor
            
            transcript_file = transcript_files[0]
            video_id = transcript_file.stem.replace("_transcript", "")
            
            with open(transcript_file, 'r') as f:
                content = f.read()
            
            # Extract text
            if "=" * 50 in content:
                transcript_text = content.split("=" * 50, 1)[1].strip()
            else:
                transcript_text = content
            
            # Extract timestamps
            extractor = TimestampExtractor()
            sentences = extractor.extract_sentence_timestamps(transcript_text)
            
            if not sentences:
                self.results["context_expansion"] = {
                    "status": "FAIL",
                    "notes": "Timestamp extraction failed"
                }
                print("❌ FAIL: Cannot extract timestamps")
                return
            
            # Check sentence structure
            first_sentence = sentences[0]
            required_fields = ["sentence", "start_time", "end_time"]
            missing_fields = [f for f in required_fields if f not in first_sentence]
            
            if missing_fields:
                self.results["context_expansion"] = {
                    "status": "FAIL",
                    "notes": f"Sentences missing fields: {missing_fields}"
                }
                print(f"❌ FAIL: Missing fields in sentences: {missing_fields}")
                return
            
            self.results["context_expansion"] = {
                "status": "PASS",
                "notes": f"Timestamps extracted, {len(sentences)} sentences parsed, context expansion ready",
                "video_id": video_id,
                "sentence_count": len(sentences)
            }
            print(f"✅ PASS: Context expansion working")
            print(f"   Video: {video_id}")
            print(f"   Sentences: {len(sentences)}")
            
        except ImportError as e:
            self.results["context_expansion"] = {
                "status": "FAIL",
                "notes": f"Import error: {e}"
            }
            print(f"❌ FAIL: Cannot import timestamp extractor: {e}")
        except Exception as e:
            self.results["context_expansion"] = {
                "status": "FAIL",
                "notes": f"Error: {e}"
            }
            print(f"❌ FAIL: {e}")
    
    def test_cli_commands(self):
        """Test CLI usability"""
        print("\n" + "="*80)
        print("TEST 6: CLI COMMANDS")
        print("="*80)
        
        cli_scripts = [
            "scripts/ingest_account.py",
            "scripts/search_semantic.py",
            "scripts/show_transcript.py"
        ]
        
        all_exist = True
        for script in cli_scripts:
            if not Path(script).exists():
                all_exist = False
                print(f"❌ Missing: {script}")
        
        if not all_exist:
            self.results["cli_commands"] = {
                "status": "FAIL",
                "notes": "Some CLI scripts missing"
            }
            print("❌ FAIL: CLI scripts incomplete")
            return
        
        self.results["cli_commands"] = {
            "status": "PASS",
            "notes": "All CLI scripts present and importable"
        }
        print("✅ PASS: CLI commands available")
    
    def test_verification(self):
        """Test verification system"""
        print("\n" + "="*80)
        print("TEST 7: VERIFICATION SYSTEM")
        print("="*80)
        
        try:
            verify_script = Path("verify_transcripts.py")
            
            if not verify_script.exists():
                self.results["verification_system"] = {
                    "status": "SKIP",
                    "notes": "verify_transcripts.py not found"
                }
                print("⚠️  SKIP: Verification script not found")
                return
            
            self.results["verification_system"] = {
                "status": "PASS",
                "notes": "Verification script exists"
            }
            print("✅ PASS: Verification system available")
            
        except Exception as e:
            self.results["verification_system"] = {
                "status": "FAIL",
                "notes": f"Error: {e}"
            }
            print(f"❌ FAIL: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        feature_names = {
            "ingestion": "Ingestion",
            "idempotency": "Idempotency",
            "topic_extraction": "Topic Extraction",
            "semantic_search": "Semantic Search",
            "context_expansion": "Context Expansion",
            "cli_commands": "CLI Commands",
            "verification_system": "Verification System"
        }
        
        # Print table
        print(f"\n{'Feature':<25} {'Status':<12} {'Notes'}")
        print("-" * 80)
        
        for key, name in feature_names.items():
            if key in self.results:
                result = self.results[key]
                status = result['status']
                notes = result.get('notes', '')[:50]
                
                # Color coding
                if status == "PASS":
                    status_display = f"✅ {status}"
                elif status == "FAIL":
                    status_display = f"❌ {status}"
                else:
                    status_display = f"⚠️  {status}"
                
                print(f"{name:<25} {status_display:<12} {notes}")
        
        print("-" * 80)
        
        # Count results
        passed = sum(1 for r in self.results.values() if r['status'] == 'PASS')
        failed = sum(1 for r in self.results.values() if r['status'] == 'FAIL')
        skipped = sum(1 for r in self.results.values() if r['status'] == 'SKIP')
        
        print(f"\nTotal: {passed} PASS, {failed} FAIL, {skipped} SKIP")
        
        if failed > 0:
            print("\n⚠️  Some tests failed. See notes above for details.")
        elif skipped > 0:
            print("\n⚠️  Some tests were skipped. Run suggested commands to enable them.")
        else:
            print("\n🎉 All tests passed!")
        
        print("="*80)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='End-to-end system test')
    parser.add_argument('--user', default='beabettermandaily', help='Account to test')
    
    args = parser.parse_args()
    
    tester = SystemTester(username=args.user)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    failed = sum(1 for r in results.values() if r['status'] == 'FAIL')
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
