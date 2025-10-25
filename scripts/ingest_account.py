#!/usr/bin/env python3
"""
Idempotent TikTok Account Ingestion Script
Only processes new videos, skips already-transcribed content
Uses index.json as source of truth
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Any

# Add parent directory to path to import tiktok_transcriber
sys.path.insert(0, str(Path(__file__).parent.parent))

from tiktok_transcriber import TikTokTranscriber


class IdempotentIngestionManager:
    """Manages idempotent ingestion with index.json tracking"""
    
    def __init__(self, username: str, base_dir: str = "accounts"):
        """
        Initialize ingestion manager
        
        Args:
            username: TikTok username
            base_dir: Base directory for accounts
        """
        self.username = username.lstrip('@')
        self.base_dir = Path(base_dir)
        self.account_dir = self.base_dir / self.username
        self.transcriptions_dir = self.account_dir / "transcriptions"
        self.index_file = self.account_dir / "index.json"
        
        # Create directories
        self.account_dir.mkdir(parents=True, exist_ok=True)
        self.transcriptions_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize index
        self.index = self._load_index()
        
    def _load_index(self) -> Dict[str, Any]:
        """Load index.json or create new one"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load index.json: {e}, creating new index")
        
        # Create new index
        return {
            "account": self.username,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "processed_videos": {},
            "stats": {
                "total_videos_found": 0,
                "total_processed": 0,
                "total_skipped": 0,
                "total_failed": 0,
                "last_ingestion_date": None
            }
        }
    
    def _save_index(self):
        """Save index.json"""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, default=str)
    
    def get_processed_video_ids(self) -> Set[str]:
        """Get set of already-processed video IDs"""
        return set(self.index.get("processed_videos", {}).keys())
    
    def filter_new_videos(self, all_videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out already-processed videos"""
        processed_ids = self.get_processed_video_ids()
        new_videos = [v for v in all_videos if v.get('video_id') not in processed_ids]
        return new_videos
    
    def mark_video_processed(self, video_id: str, metadata: Dict[str, Any], success: bool):
        """Mark a video as processed in the index"""
        if "processed_videos" not in self.index:
            self.index["processed_videos"] = {}
        
        self.index["processed_videos"][video_id] = {
            "video_id": video_id,
            "title": metadata.get("title", ""),
            "processed_at": datetime.now().isoformat(),
            "success": success,
            "transcript_file": f"{video_id}_transcript.txt" if success else None,
            "transcription_length": metadata.get("transcription_length", 0) if success else 0,
            "duration": metadata.get("duration", 0),
            "url": metadata.get("url", "")
        }
        
        # Update stats
        if success:
            self.index["stats"]["total_processed"] = \
                self.index["stats"].get("total_processed", 0) + 1
        else:
            self.index["stats"]["total_failed"] = \
                self.index["stats"].get("total_failed", 0) + 1
    
    def ingest_account(self, 
                      max_videos: int = None,
                      model_size: str = "small",
                      cookies_file: str = None,
                      min_speech_threshold: int = 50,
                      verbose: bool = False) -> Dict[str, Any]:
        """
        Ingest new videos for account (idempotent)
        
        Args:
            max_videos: Maximum videos to fetch
            model_size: Whisper model size
            cookies_file: Path to cookies.txt
            min_speech_threshold: Minimum speech characters
            verbose: Verbose logging
            
        Returns:
            Ingestion results
        """
        start_time = datetime.now()
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        print(f"\n{'='*80}")
        print(f"🔄 IDEMPOTENT INGESTION: @{self.username}")
        print(f"{'='*80}")
        print(f"Account directory: {self.account_dir}")
        print(f"Index file: {self.index_file}")
        print(f"Previously processed: {len(self.get_processed_video_ids())} videos")
        print(f"{'='*80}\n")
        
        # Initialize transcriber
        transcriber = TikTokTranscriber(
            output_dir=str(self.base_dir),
            model_size=model_size,
            max_videos=max_videos,
            cookies_file=cookies_file,
            min_speech_threshold=min_speech_threshold
        )
        
        # Fetch all available videos
        logging.info(f"Fetching video list for @{self.username}...")
        all_videos = transcriber.fetch_account_videos(self.username)
        
        if not all_videos:
            print(f"❌ No videos found for @{self.username}")
            return {
                "error": "No videos found",
                "stats": self.index["stats"]
            }
        
        # Update total videos found
        self.index["stats"]["total_videos_found"] = len(all_videos)
        
        # Filter out already-processed videos
        new_videos = self.filter_new_videos(all_videos)
        already_processed = len(all_videos) - len(new_videos)
        
        print(f"📊 Video Analysis:")
        print(f"   Total videos found: {len(all_videos)}")
        print(f"   Already processed: {already_processed} (SKIPPED)")
        print(f"   New videos to process: {len(new_videos)}")
        print(f"{'='*80}\n")
        
        if not new_videos:
            print(f"✅ All videos already processed! Nothing to do.")
            print(f"{'='*80}\n")
            return {
                "account": self.username,
                "all_videos": len(all_videos),
                "already_processed": already_processed,
                "newly_processed": 0,
                "skipped": 0,
                "failed": 0,
                "duration": 0,
                "stats": self.index["stats"]
            }
        
        # Process only new videos
        newly_processed = 0
        newly_skipped = 0
        newly_failed = 0
        
        transcriber.output_dir = self.transcriptions_dir
        
        for i, video in enumerate(new_videos, 1):
            video_id = video.get('video_id')
            print(f"[{i}/{len(new_videos)}] Processing: {video.get('title', 'Unknown')[:60]}...")
            
            try:
                result = transcriber.process_single_video(video)
                
                # Merge video metadata into result
                result_with_metadata = {**result, **video}
                
                if result.get('success'):
                    self.mark_video_processed(video_id, result_with_metadata, True)
                    newly_processed += 1
                    print(f"    ✅ Transcribed ({result.get('transcription_length', 0)} chars)")
                elif result.get('skipped'):
                    self.mark_video_processed(video_id, result_with_metadata, False)
                    newly_skipped += 1
                    print(f"    ⏭️  Skipped (no speech)")
                else:
                    self.mark_video_processed(video_id, result_with_metadata, False)
                    newly_failed += 1
                    print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
                
                # Save index after each video
                self._save_index()
                
            except Exception as e:
                logging.error(f"Error processing video {video_id}: {e}")
                self.mark_video_processed(video_id, {"error": str(e)}, False)
                newly_failed += 1
                print(f"    ❌ Error: {e}")
                self._save_index()
        
        # Update final stats
        self.index["stats"]["last_ingestion_date"] = datetime.now().isoformat()
        self.index["stats"]["total_skipped"] = \
            self.index["stats"].get("total_skipped", 0) + newly_skipped
        self._save_index()
        
        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"✅ INGESTION COMPLETE")
        print(f"{'='*80}")
        print(f"Found {len(all_videos)} total videos")
        print(f"{already_processed} already processed → SKIPPED")
        print(f"{newly_processed} new videos → TRANSCRIBED and SAVED")
        print(f"{newly_skipped} videos → SKIPPED (no speech)")
        print(f"{newly_failed} videos → FAILED")
        print(f"✅ Completed in {duration:.0f}s ({duration/60:.1f}m)")
        print(f"{'='*80}\n")
        
        return {
            "account": self.username,
            "all_videos": len(all_videos),
            "already_processed": already_processed,
            "newly_processed": newly_processed,
            "newly_skipped": newly_skipped,
            "newly_failed": newly_failed,
            "duration": duration,
            "stats": self.index["stats"]
        }


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Idempotent TikTok Account Ingestion - Only processes new videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # First run - processes all videos
  python scripts/ingest_account.py --user kwrt_
  
  # Second run - skips already processed, only gets new ones
  python scripts/ingest_account.py --user kwrt_
  
  # With options
  python scripts/ingest_account.py --user matrix.v5 --max-videos 50
  python scripts/ingest_account.py --user beabettermandaily --cookies cookies.txt
  
  # Verbose mode
  python scripts/ingest_account.py --user kwrt_ -v

Features:
  - ✅ Idempotent: Running twice does zero extra work
  - ✅ Resumable: Can stop and resume anytime
  - ✅ Append-only: Only processes new videos
  - ✅ Fast: Skips downloads and transcription for existing videos
  - ✅ Safe: Updates index after each video (crash-resistant)
        """
    )
    
    parser.add_argument('--user', '-u', required=True,
                       help='TikTok username (with or without @)')
    parser.add_argument('--base-dir', default='accounts',
                       help='Base directory for accounts (default: accounts)')
    parser.add_argument('--max-videos', type=int, default=None,
                       help='Maximum videos to fetch (default: 10 or from env)')
    parser.add_argument('--model-size', default='small',
                       choices=['tiny', 'small', 'medium', 'large'],
                       help='Whisper model size (default: small)')
    parser.add_argument('--cookies', dest='cookies_file', default=None,
                       help='Path to cookies.txt for authenticated scraping')
    parser.add_argument('--min-speech', type=int, default=50,
                       help='Minimum characters to consider video has speech (default: 50)')
    parser.add_argument('--with-topics', action='store_true',
                       help='Extract topics after ingestion (Step 2)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create manager and run ingestion
    manager = IdempotentIngestionManager(args.user, args.base_dir)
    
    results = manager.ingest_account(
        max_videos=args.max_videos,
        model_size=args.model_size,
        cookies_file=args.cookies_file,
        min_speech_threshold=args.min_speech,
        verbose=args.verbose
    )
    
    # Extract topics if requested
    if args.with_topics and not results.get("error"):
        newly_processed = results.get('newly_processed', 0)
        already_processed = results.get('already_processed', 0)
        
        if newly_processed > 0 or already_processed > 0:
            print(f"\n{'='*60}")
            print(f"🧠 Extracting topics...")
            print(f"{'='*60}\n")
            
            try:
                # Import here to avoid loading NLP libraries if not needed
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from topic_extractor import AccountTopicManager
                
                topic_manager = AccountTopicManager(args.user, args.base_dir)
                topic_results = topic_manager.extract_all_topics(force=False)
                
                print(f"✅ Topics extracted:")
                print(f"   - {topic_results['extracted']} videos processed")
                print(f"   - {topic_results['skipped']} videos skipped (already had topics)")
                if topic_results['failed'] > 0:
                    print(f"   - {topic_results['failed']} videos failed")
                
            except ImportError:
                print(f"⚠️  Topic extraction requires additional libraries")
                print(f"   Install with: pip install keybert sentence-transformers scikit-learn nltk")
            except Exception as e:
                print(f"⚠️  Topic extraction failed: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
    
    # Exit with appropriate code
    if results.get("error"):
        sys.exit(1)
    elif results.get("newly_failed", 0) > 0:
        sys.exit(2)  # Some videos failed
    else:
        sys.exit(0)  # Success


if __name__ == "__main__":
    main()

