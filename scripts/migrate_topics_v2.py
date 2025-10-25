#!/usr/bin/env python3
"""
Migration Script - Convert V1 topics to V2 format

This script migrates existing topic data to the enhanced V2 format with:
- Canonical forms
- Confidence scores
- Timestamped evidence
- Source tracking

Usage:
    python scripts/migrate_topics_v2.py --account kwrt_ [--dry-run]
    python scripts/migrate_topics_v2.py --all [--dry-run]
    python scripts/migrate_topics_v2.py --account kwrt_ --force  # Overwrite existing V2 data
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import asdict
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from topic_extractor_v2 import TopicExtractorV2, EnhancedTopic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class TopicMigrator:
    """Migrates topic data from V1 to V2 format"""
    
    def __init__(self, dry_run: bool = False, force: bool = False):
        """
        Args:
            dry_run: If True, only simulate migration without writing files
            force: If True, overwrite existing V2 data
        """
        self.dry_run = dry_run
        self.force = force
        self.extractor = TopicExtractorV2()
        self.stats = {
            'accounts_migrated': 0,
            'videos_migrated': 0,
            'videos_skipped': 0,
            'videos_failed': 0
        }
        
    def migrate_account(self, username: str) -> bool:
        """
        Migrate all topic data for an account
        
        Args:
            username: TikTok username
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Migrating @{username}")
        logger.info(f"{'='*60}")
        
        account_dir = Path(f"accounts/{username}")
        if not account_dir.exists():
            logger.error(f"Account directory not found: {account_dir}")
            return False
            
        # Check if index.json exists
        index_file = account_dir / "index.json"
        if not index_file.exists():
            logger.warning(f"No index.json found for @{username}")
            return False
            
        # Load index
        with open(index_file) as f:
            index_data = json.load(f)
            
        # Handle both formats: processed_videos (dict) or videos (list)
        processed_videos = index_data.get('processed_videos', {})
        if processed_videos:
            videos = list(processed_videos.values())
        else:
            videos = index_data.get('videos', [])
            
        logger.info(f"Found {len(videos)} videos in index")
        
        # Migrate each video
        videos_migrated = 0
        videos_skipped = 0
        videos_failed = 0
        
        for video in videos:
            video_id = video.get('video_id')
            if not video_id:
                continue
                
            # Check if transcript exists
            transcript_file = account_dir / "transcriptions" / f"{video_id}_transcript.txt"
            if not transcript_file.exists():
                logger.debug(f"No transcript for {video_id}, skipping")
                videos_skipped += 1
                continue
                
            # Check if V1 tags exist
            v1_tags_file = account_dir / "topics" / f"{video_id}_tags.json"
            if not v1_tags_file.exists():
                logger.debug(f"No V1 tags for {video_id}, generating from scratch")
                
            # Check if V2 tags already exist
            v2_tags_file = account_dir / "topics" / f"{video_id}_tags_v2.json"
            if v2_tags_file.exists() and not self.force:
                logger.debug(f"V2 tags already exist for {video_id}, skipping")
                videos_skipped += 1
                continue
                
            # Migrate this video
            try:
                self._migrate_video(
                    username=username,
                    video_id=video_id,
                    video_title=video.get('title', ''),
                    transcript_file=transcript_file,
                    v1_tags_file=v1_tags_file if v1_tags_file.exists() else None,
                    output_file=v2_tags_file
                )
                videos_migrated += 1
            except Exception as e:
                logger.error(f"Failed to migrate {video_id}: {e}")
                videos_failed += 1
                continue
                
        # Update aggregated account tags
        if videos_migrated > 0 and not self.dry_run:
            self._aggregate_account_tags_v2(username, account_dir)
            
        logger.info(f"\nMigration complete for @{username}:")
        logger.info(f"  ✓ Migrated: {videos_migrated}")
        logger.info(f"  ⊘ Skipped: {videos_skipped}")
        logger.info(f"  ✗ Failed: {videos_failed}")
        
        self.stats['accounts_migrated'] += 1
        self.stats['videos_migrated'] += videos_migrated
        self.stats['videos_skipped'] += videos_skipped
        self.stats['videos_failed'] += videos_failed
        
        return videos_failed == 0
        
    def _migrate_video(self,
                       username: str,
                       video_id: str,
                       video_title: str,
                       transcript_file: Path,
                       v1_tags_file: Path,
                       output_file: Path):
        """Migrate a single video's tags to V2 format"""
        
        # Read transcript
        with open(transcript_file, 'r') as f:
            transcript_text = f.read()
            
        # Extract timestamps if available (from transcript format)
        timestamps = self._extract_timestamps_from_transcript(transcript_text)
        
        # Extract V2 topics
        logger.debug(f"Extracting V2 topics for {video_id}...")
        enhanced_topics = self.extractor.extract_video_topics_enhanced(
            transcript=transcript_text,
            sentence_timestamps=timestamps,
            title=video_title,
            video_id=video_id
        )
        
        # Convert to JSON-serializable format
        topics_list = []
        for topic in enhanced_topics:
            topic_dict = {
                'tag': topic.tag,
                'canonical': topic.canonical,
                'confidence': topic.confidence,
                'score': topic.score,
                'type': 'keyphrase',
                'source': 'transcript',
                'evidence': [
                    {
                        'sentence_index': ev.sentence_index,
                        'start_time': ev.start_time,
                        'end_time': ev.end_time,
                        'text': ev.text
                    }
                    for ev in topic.evidence
                ] if topic.evidence else []
            }
            topics_list.append(topic_dict)
            
        # Create V2 output structure
        v2_data = {
            'video_id': video_id,
            'title': video_title,
            'format_version': '2.0',
            'extractor': 'topic_extractor_v2',
            'total_topics': len(topics_list),
            'tags': topics_list
        }
        
        # Write to file (unless dry run)
        if self.dry_run:
            logger.info(f"[DRY RUN] Would write {len(topics_list)} topics to {output_file}")
        else:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(v2_data, f, indent=2)
            logger.debug(f"✓ Wrote {len(topics_list)} topics to {output_file}")
            
    def _extract_timestamps_from_transcript(self, transcript_text: str) -> List[Dict]:
        """
        Extract timestamps from transcript if available
        
        Returns:
            List of {start_time, end_time, text} dicts
        """
        # Simple implementation - assumes transcript may have [MM:SS] markers
        # If no markers, returns empty list (extractor will work without timestamps)
        timestamps = []
        
        lines = transcript_text.split('\n')
        for line in lines:
            if line.strip():
                # Check for [MM:SS] or (MM:SS) timestamp markers
                import re
                match = re.search(r'[\[\(](\d+):(\d+)[\]\)]', line)
                if match:
                    minutes = int(match.group(1))
                    seconds = int(match.group(2))
                    start_seconds = minutes * 60 + seconds
                    
                    # Extract text after timestamp
                    text = re.sub(r'[\[\(]\d+:\d+[\]\)]', '', line).strip()
                    
                    timestamps.append({
                        'start_time': start_seconds,
                        'end_time': start_seconds + 5,  # Estimate 5 second segments
                        'text': text
                    })
                else:
                    # No timestamp, add as plain text segment
                    timestamps.append({
                        'start_time': len(timestamps) * 5,  # Estimate
                        'end_time': (len(timestamps) + 1) * 5,
                        'text': line.strip()
                    })
                    
        return timestamps
        
    def _aggregate_account_tags_v2(self, username: str, account_dir: Path):
        """Aggregate all V2 video tags into account-level file"""
        
        logger.info(f"Aggregating V2 tags for @{username}...")
        
        topics_dir = account_dir / "topics"
        
        # Collect all V2 tag files
        v2_files = list(topics_dir.glob("*_tags_v2.json"))
        
        if not v2_files:
            logger.warning("No V2 tag files found to aggregate")
            return
            
        # Aggregate topics
        canonical_topics = {}  # canonical -> {frequency, videos, scores, etc}
        total_videos = 0
        
        for tag_file in v2_files:
            with open(tag_file) as f:
                data = json.load(f)
                
            video_id = data.get('video_id')
            total_videos += 1
            
            for tag_data in data.get('tags', []):
                canonical = tag_data.get('canonical', tag_data['tag'])
                
                if canonical not in canonical_topics:
                    canonical_topics[canonical] = {
                        'canonical': canonical,
                        'variants': set(),
                        'frequency': 0,
                        'scores': [],
                        'confidences': [],
                        'video_ids': set(),
                        'sources': set()
                    }
                    
                ct = canonical_topics[canonical]
                ct['variants'].add(tag_data['tag'])
                ct['frequency'] += 1
                ct['scores'].append(tag_data.get('score', 0.5))
                ct['confidences'].append(tag_data.get('confidence', 0.5))
                ct['video_ids'].add(video_id)
                ct['sources'].add(tag_data.get('source', 'transcript'))
                
        # Convert to list and compute averages
        aggregated_topics = []
        for canonical, data in canonical_topics.items():
            aggregated_topics.append({
                'canonical': canonical,
                'variants': sorted(list(data['variants'])),
                'frequency': data['frequency'],
                'avg_score': sum(data['scores']) / len(data['scores']),
                'avg_confidence': sum(data['confidences']) / len(data['confidences']),
                'video_ids': sorted(list(data['video_ids'])),
                'sources': sorted(list(data['sources']))
            })
            
        # Sort by frequency
        aggregated_topics.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Write aggregated file
        output_file = topics_dir / "account_tags_v2.json"
        output_data = {
            'username': username,
            'format_version': '2.0',
            'total_canonical_topics': len(aggregated_topics),
            'total_videos': total_videos,
            'topics': aggregated_topics
        }
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would write {len(aggregated_topics)} canonical topics to {output_file}")
        else:
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"✓ Wrote {len(aggregated_topics)} canonical topics to {output_file}")
            
    def migrate_all_accounts(self) -> Dict[str, bool]:
        """
        Migrate all accounts in accounts/ directory
        
        Returns:
            Dictionary mapping username -> success status
        """
        accounts_dir = Path("accounts")
        
        if not accounts_dir.exists():
            logger.error("accounts/ directory not found")
            return {}
            
        # Find all accounts
        accounts = []
        for account_dir in accounts_dir.iterdir():
            if account_dir.is_dir() and (account_dir / "index.json").exists():
                accounts.append(account_dir.name)
                
        logger.info(f"Found {len(accounts)} accounts to migrate")
        
        results = {}
        for username in accounts:
            try:
                success = self.migrate_account(username)
                results[username] = success
            except Exception as e:
                logger.error(f"Failed to migrate @{username}: {e}")
                results[username] = False
                
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info("MIGRATION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Accounts migrated: {self.stats['accounts_migrated']}")
        logger.info(f"Videos migrated: {self.stats['videos_migrated']}")
        logger.info(f"Videos skipped: {self.stats['videos_skipped']}")
        logger.info(f"Videos failed: {self.stats['videos_failed']}")
        
        return results


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Migrate topic data from V1 to V2 format"
    )
    parser.add_argument(
        '--account',
        help='Migrate specific account (username)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Migrate all accounts'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without writing files'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing V2 data'
    )
    
    args = parser.parse_args()
    
    if not args.account and not args.all:
        parser.error("Must specify either --account or --all")
        
    migrator = TopicMigrator(dry_run=args.dry_run, force=args.force)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No files will be written")
        
    if args.account:
        success = migrator.migrate_account(args.account)
        exit(0 if success else 1)
    else:
        results = migrator.migrate_all_accounts()
        failures = [u for u, success in results.items() if not success]
        exit(0 if not failures else 1)


if __name__ == '__main__':
    main()
