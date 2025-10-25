#!/usr/bin/env python3
"""
Extract Topics CLI - Extract semantic topics from transcribed videos
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from topic_extractor import AccountTopicManager


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Extract semantic topics from transcribed TikTok videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract topics for an account
  python scripts/extract_topics.py --user kwrt_
  
  # Force re-extraction (ignore existing topics)
  python scripts/extract_topics.py --user kwrt_ --force
  
  # With verbose logging
  python scripts/extract_topics.py --user kwrt_ -v

How it works:
  1. Reads transcripts from accounts/<username>/transcriptions/
  2. Uses KeyBERT + sentence-transformers for semantic extraction
  3. Extracts 3-10 topics per video
  4. Saves to accounts/<username>/topics/<video_id>_topics.json
  5. Generates account_topics.json (ranked topics)
  6. Creates umbrella_topics.json (grouped categories)

Output structure:
  accounts/<username>/topics/
  ├── <video_id>_topics.json     (per-video topics)
  ├── account_topics.json         (ranked aggregation)
  └── umbrella_topics.json        (semantic clusters)
        """
    )
    
    parser.add_argument('--user', '-u', required=True,
                       help='TikTok username (with or without @)')
    parser.add_argument('--base-dir', default='accounts',
                       help='Base directory for accounts (default: accounts)')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force re-extraction even if topics exist')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    username = args.user.lstrip('@')
    
    print(f"\n{'='*80}")
    print(f"🧠 TOPIC EXTRACTION: @{username}")
    print(f"{'='*80}\n")
    
    try:
        # Initialize manager
        manager = AccountTopicManager(username, args.base_dir)
        
        # Extract topics
        results = manager.extract_all_topics(force=args.force)
        
        # Print results
        print(f"📊 Extraction Results:")
        print(f"   Total videos: {results['total_videos']}")
        print(f"   ✅ Extracted: {results['extracted']}")
        print(f"   ⏭️  Skipped (already exist): {results['skipped']}")
        print(f"   ❌ Failed: {results['failed']}")
        
        if results['extracted'] > 0 or results['skipped'] > 0:
            print(f"\n📁 Output saved to:")
            topics_dir = Path(args.base_dir) / username / "topics"
            print(f"   {topics_dir}")
            print(f"   ├── <video_id>_tags.json ({results['extracted'] + results['skipped']} files)")
            print(f"   ├── account_tags.json")
            print(f"   └── account_category.json")
        
        print(f"\n{'='*80}")
        
        if results['failed'] > 0:
            print(f"⚠️  {results['failed']} video(s) failed extraction")
            sys.exit(2)
        elif results['extracted'] == 0 and results['skipped'] == 0:
            print(f"❌ No tags extracted")
            sys.exit(1)
        else:
            print(f"✅ Tag extraction & category classification complete!")
            print(f"\nNext steps:")
            print(f"  - View category: python scripts/list_topics.py --user {username} --category")
            print(f"  - View tags: python scripts/list_topics.py --user {username}")
            print(f"  - View all: python scripts/list_topics.py --user {username} --all")
            sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\nMake sure you've run ingestion first:")
        print(f"  python scripts/ingest_account.py --user {username}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

