#!/usr/bin/env python3
"""
Show Transcript CLI - Display full transcript with highlighting and auto-scroll
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.semantic_search.engine import SemanticSearchEngine
from core.semantic_search.timestamp_extractor import TimestampExtractor


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Show full transcript with highlighting and auto-scroll',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show full transcript for a video
  python scripts/show_transcript.py --video 7557947251092409613 --username kwrt_
  
  # Jump to specific timestamp
  python scripts/show_transcript.py --video 7557947251092409613 --username kwrt_ --jump 00:41
  
  # Jump to specific time in seconds
  python scripts/show_transcript.py --video 7557947251092409613 --username kwrt_ --jump 41
  
  # Show with context around match
  python scripts/show_transcript.py --video 7557947251092409613 --username kwrt_ --jump 00:41 --context 5

How it works:
  1. Loads full transcript from accounts/{username}/transcriptions/
  2. Extracts sentence-level timestamps
  3. Highlights the matched section with >>> <<<
  4. Shows 4-6 sentences of context around the match
        """
    )
    
    parser.add_argument('--video', required=True, help='Video ID')
    parser.add_argument('--username', required=True, help='Account username')
    parser.add_argument('--jump', help='Timestamp to jump to (MM:SS or seconds)')
    parser.add_argument('--context', type=int, default=3, help='Number of sentences before/after match')
    parser.add_argument('--base-dir', default='accounts', help='Base directory for accounts')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print(f"\n{'='*80}")
    print(f"📄 TRANSCRIPT VIEWER")
    print(f"{'='*80}\n")
    
    try:
        # Show transcript
        show_transcript(
            video_id=args.video,
            username=args.username,
            jump_time=args.jump,
            context_size=args.context,
            base_dir=args.base_dir
        )
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def show_transcript(video_id: str, username: str, jump_time: Optional[str] = None, 
                   context_size: int = 3, base_dir: str = "accounts"):
    """Show transcript with optional highlighting"""
    
    # Load transcript
    transcript_path = Path(base_dir) / username / "transcriptions" / f"{video_id}_transcript.txt"
    
    if not transcript_path.exists():
        print(f"❌ Transcript not found: {transcript_path}")
        return
    
    # Read transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_content = f.read()
    
    # Extract transcript text (skip header)
    if "=" * 50 in transcript_content:
        transcript_text = transcript_content.split("=" * 50, 1)[1].strip()
    else:
        transcript_text = transcript_content
    
    if not transcript_text:
        print("❌ Empty transcript")
        return
    
    # Extract timestamps
    timestamp_extractor = TimestampExtractor()
    sentences = timestamp_extractor.extract_sentence_timestamps(transcript_text)
    
    print(f"📹 Video: {video_id}")
    print(f"👤 Username: @{username}")
    print(f"📊 Total sentences: {len(sentences)}")
    
    if jump_time:
        # Find target sentence
        target_time = parse_timestamp(jump_time)
        target_sentence = find_sentence_by_time(sentences, target_time)
        
        if target_sentence:
            print(f"🎯 Jumping to: {jump_time}")
            show_context_around_sentence(sentences, target_sentence, context_size)
        else:
            print(f"⚠️  No sentence found at {jump_time}")
            print("📄 Showing full transcript:")
            show_full_transcript(sentences)
    else:
        print("📄 Full transcript:")
        show_full_transcript(sentences)


def parse_timestamp(time_str: str) -> float:
    """Parse timestamp string to seconds"""
    if ':' in time_str:
        # Format: MM:SS
        parts = time_str.split(':')
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
    else:
        # Format: seconds
        return float(time_str)
    
    return 0.0


def find_sentence_by_time(sentences: List[Dict[str, Any]], target_time: float) -> Optional[Dict[str, Any]]:
    """Find sentence closest to target time"""
    if not sentences:
        return None
    
    # Find sentence with start_time closest to target_time
    closest_sentence = None
    min_diff = float('inf')
    
    for sentence in sentences:
        start_time = sentence.get("start_time", 0)
        diff = abs(start_time - target_time)
        
        if diff < min_diff:
            min_diff = diff
            closest_sentence = sentence
    
    return closest_sentence


def show_context_around_sentence(sentences: List[Dict[str, Any]], target_sentence: Dict[str, Any], 
                                context_size: int):
    """Show context around a target sentence with highlighting"""
    target_index = target_sentence.get("sentence_index", 0)
    
    # Calculate context range
    start_idx = max(0, target_index - context_size)
    end_idx = min(len(sentences), target_index + context_size + 1)
    
    print(f"\n🎯 Context around sentence {target_index + 1}:")
    print(f"⏰ Time: {format_timestamp(target_sentence.get('start_time', 0))}")
    print("-" * 80)
    
    for i in range(start_idx, end_idx):
        sentence = sentences[i]
        text = sentence["sentence"]
        timestamp = format_timestamp(sentence.get("start_time", 0))
        
        if i == target_index:
            # Highlight target sentence
            print(f">>> {text} <<<")
        else:
            print(f"    {text}")
        
        if i < end_idx - 1:  # Don't print separator after last sentence
            print()


def show_full_transcript(sentences: List[Dict[str, Any]]):
    """Show full transcript"""
    print("-" * 80)
    
    for i, sentence in enumerate(sentences):
        text = sentence["sentence"]
        timestamp = format_timestamp(sentence.get("start_time", 0))
        
        print(f"[{timestamp}] {text}")
        print()


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    main()
