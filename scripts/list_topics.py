#!/usr/bin/env python3
"""
List Topics CLI - View extracted topics for TikTok accounts
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any


def load_account_tags(username: str, base_dir: str = "accounts") -> Dict[str, Any]:
    """Load account tags"""
    tags_file = Path(base_dir) / username / "topics" / "account_tags.json"
    
    if not tags_file.exists():
        raise FileNotFoundError(f"Tags not found. Run: python scripts/extract_topics.py --user {username}")
    
    with open(tags_file, 'r') as f:
        return json.load(f)


def load_account_category(username: str, base_dir: str = "accounts") -> Dict[str, Any]:
    """Load account category"""
    category_file = Path(base_dir) / username / "topics" / "account_category.json"
    
    if not category_file.exists():
        return None
    
    with open(category_file, 'r') as f:
        return json.load(f)


def load_video_tags(username: str, base_dir: str = "accounts") -> list:
    """Load all video tags"""
    topics_dir = Path(base_dir) / username / "topics"
    
    if not topics_dir.exists():
        return []
    
    video_tags = []
    for tag_file in topics_dir.glob("*_tags.json"):
        if tag_file.name in ["account_tags.json", "account_category.json"]:
            continue
        
        with open(tag_file, 'r') as f:
            video_tags.append(json.load(f))
    
    return video_tags


def print_account_tags(account_tags: Dict[str, Any], top_n: int = 20):
    """Print ranked account tags"""
    print(f"\n{'='*80}")
    print(f"🏷️  ACCOUNT TAGS (Top {top_n})")
    print(f"{'='*80}\n")
    
    print(f"Total unique tags: {account_tags['total_tags']}")
    print(f"Total videos: {account_tags['total_videos']}")
    print()
    
    for i, tag_data in enumerate(account_tags['tags'][:top_n], 1):
        tag = tag_data['tag']
        freq = tag_data['frequency']
        score = tag_data['combined_score']
        
        # Create bar visualization
        max_freq = account_tags['tags'][0]['frequency']
        bar_length = int((freq / max_freq) * 30)
        bar = '█' * bar_length
        
        print(f"{i:2}. {tag:40} │ {bar} ({freq} videos, score: {score:.2f})")
    
    if account_tags['total_tags'] > top_n:
        remaining = account_tags['total_tags'] - top_n
        print(f"\n... and {remaining} more tags")


def print_account_category(category: Dict[str, Any]):
    """Print account category classification"""
    if not category:
        print("\n⚠️  No category classification found")
        return
    
    print(f"\n{'='*80}")
    print("📂 ACCOUNT CATEGORY")
    print(f"{'='*80}\n")
    
    print(f"Category: {category['category']}")
    print(f"Confidence: {category['confidence']:.1%}\n")
    
    # Show top 5 scores
    all_scores = category.get('all_scores', {})
    sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print("Top matches:")
    for cat_name, score in sorted_scores:
        bar_len = int(score * 40)
        bar = "█" * bar_len
        print(f"  {cat_name:<20} {bar} {score:.1%}")


def print_video_tags(video_tags: list, show_all: bool = False):
    """Print per-video tags"""
    print(f"\n{'='*80}")
    print(f"🎬 PER-VIDEO TAGS ({len(video_tags)} videos)")
    print(f"{'='*80}\n")
    
    display_count = len(video_tags) if show_all else min(5, len(video_tags))
    
    for i, video_data in enumerate(video_tags[:display_count], 1):
        video_id = video_data['video_id']
        title = video_data.get('title', 'Unknown')[:60]
        tags = video_data['tags']
        
        print(f"{i}. {title}")
        print(f"   Video ID: {video_id}")
        print(f"   Tags ({len(tags)}): {', '.join(t['tag'] for t in tags[:5])}")
        if len(tags) > 5:
            print(f"   ... and {len(tags) - 5} more")
        print()
    
    if not show_all and len(video_tags) > 5:
        print(f"... and {len(video_tags) - 5} more videos")
        print(f"\nUse --show-all to see all videos")


def export_json(username: str, base_dir: str, output_file: str):
    """Export all tags and category to JSON"""
    account_tags = load_account_tags(username, base_dir)
    account_category = load_account_category(username, base_dir)
    video_tags = load_video_tags(username, base_dir)
    
    export_data = {
        "username": username,
        "account_category": account_category,
        "account_tags": account_tags,
        "video_tags": video_tags
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✅ Exported to: {output_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='List extracted tags and category for TikTok accounts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View top tags (default)
  python scripts/list_topics.py --user kwrt_
  
  # Show account category
  python scripts/list_topics.py --user kwrt_ --category
  
  # Show per-video tags
  python scripts/list_topics.py --user kwrt_ --by-video
  
  # Show everything
  python scripts/list_topics.py --user kwrt_ --all
  
  # Export to JSON
  python scripts/list_topics.py --user kwrt_ --export tags.json

Views:
  - Default: Top 20 account tags
  - --category: Broad category classification
  - --by-video: Tags per video
  - --all: Everything combined
        """
    )
    
    parser.add_argument('--user', '-u', required=True,
                       help='TikTok username (with or without @)')
    parser.add_argument('--base-dir', default='accounts',
                       help='Base directory for accounts (default: accounts)')
    parser.add_argument('--category', action='store_true',
                       help='Show account category classification')
    parser.add_argument('--by-video', action='store_true',
                       help='Show per-video tags')
    parser.add_argument('--all', action='store_true',
                       help='Show all views')
    parser.add_argument('--show-all', action='store_true',
                       help='Show all items (not just top N)')
    parser.add_argument('--top-n', type=int, default=20,
                       help='Number of top items to show (default: 20)')
    parser.add_argument('--export', dest='export_file',
                       help='Export all tags to JSON file')
    
    args = parser.parse_args()
    
    username = args.user.lstrip('@')
    
    try:
        # Handle export
        if args.export_file:
            export_json(username, args.base_dir, args.export_file)
            return
        
        # Print header
        print(f"\n{'='*80}")
        print(f"🧠 TAGS & CATEGORY: @{username}")
        print(f"{'='*80}")
        
        # Load data
        account_tags = load_account_tags(username, args.base_dir)
        account_category = load_account_category(username, args.base_dir)
        
        # Show requested views
        if args.all:
            print_account_category(account_category)
            print_account_tags(account_tags, args.top_n)
            video_tags = load_video_tags(username, args.base_dir)
            print_video_tags(video_tags, args.show_all)
        elif args.category:
            print_account_category(account_category)
        elif args.by_video:
            video_tags = load_video_tags(username, args.base_dir)
            print_video_tags(video_tags, args.show_all)
        else:
            # Default: show account tags
            print_account_tags(account_tags, args.top_n)
        
        print(f"\n{'='*80}\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

