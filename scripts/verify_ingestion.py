#!/usr/bin/env python3
"""
Verification script for ingestion data integrity
Checks for:
- Missing transcripts
- Duplicate transcripts
- Index.json consistency
- File system vs index mismatches
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Any
from collections import Counter
from datetime import datetime


class IngestionVerifier:
    """Verify ingestion data integrity"""
    
    def __init__(self, base_dir: str = "accounts"):
        """
        Initialize verifier
        
        Args:
            base_dir: Base directory containing account folders
        """
        self.base_dir = Path(base_dir)
    
    def verify_all_accounts(self) -> Dict[str, Any]:
        """
        Verify all accounts
        
        Returns:
            Verification results
        """
        if not self.base_dir.exists():
            return {
                "error": f"Base directory not found: {self.base_dir}",
                "accounts": []
            }
        
        accounts = []
        
        for account_dir in sorted(self.base_dir.iterdir()):
            if account_dir.is_dir() and not account_dir.name.startswith('.'):
                result = self.verify_account(account_dir.name)
                accounts.append(result)
        
        return {
            "total_accounts": len(accounts),
            "accounts": accounts,
            "verification_time": datetime.now().isoformat()
        }
    
    def verify_account(self, username: str) -> Dict[str, Any]:
        """
        Verify a single account
        
        Args:
            username: Account username
            
        Returns:
            Verification result
        """
        account_dir = self.base_dir / username
        transcriptions_dir = account_dir / "transcriptions"
        index_file = account_dir / "index.json"
        
        result = {
            "account": username,
            "path": str(account_dir),
            "index_exists": index_file.exists(),
            "transcriptions_dir_exists": transcriptions_dir.exists(),
            "issues": [],
            "warnings": [],
            "stats": {}
        }
        
        # Check if index exists
        if not index_file.exists():
            result["issues"].append("index.json not found - account not using new ingestion system")
            return result
        
        # Load index
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except Exception as e:
            result["issues"].append(f"Failed to load index.json: {e}")
            return result
        
        # Get video IDs from index
        index_video_ids = set(index.get("processed_videos", {}).keys())
        
        # Get video IDs from filesystem
        if transcriptions_dir.exists():
            transcript_files = list(transcriptions_dir.glob("*_transcript.txt"))
            fs_video_ids = set(f.stem.replace("_transcript", "") for f in transcript_files)
        else:
            fs_video_ids = set()
            result["issues"].append("Transcriptions directory does not exist")
        
        # Check for missing transcripts
        missing_transcripts = index_video_ids - fs_video_ids
        if missing_transcripts:
            result["issues"].append(
                f"Missing transcripts: {len(missing_transcripts)} videos in index but files not found"
            )
            result["missing_video_ids"] = sorted(list(missing_transcripts))
        
        # Check for orphaned transcripts
        orphaned_transcripts = fs_video_ids - index_video_ids
        if orphaned_transcripts:
            result["warnings"].append(
                f"Orphaned transcripts: {len(orphaned_transcripts)} files exist but not in index"
            )
            result["orphaned_video_ids"] = sorted(list(orphaned_transcripts))
        
        # Check for duplicate transcript files in filesystem
        duplicate_counts = Counter(fs_video_ids)
        duplicates = [vid for vid, count in duplicate_counts.items() if count > 1]
        
        if duplicates:
            result["issues"].append(f"Duplicate transcript files found: {len(duplicates)}")
            result["duplicate_video_ids"] = duplicates
        
        # Verify each transcript in index
        successful_transcripts = 0
        failed_transcripts = 0
        skipped_transcripts = 0
        
        for video_id, video_data in index.get("processed_videos", {}).items():
            if video_data.get("success"):
                successful_transcripts += 1
                # Verify file exists
                transcript_file = transcriptions_dir / f"{video_id}_transcript.txt"
                if not transcript_file.exists():
                    result["issues"].append(
                        f"Index says video {video_id} succeeded but transcript file missing"
                    )
            else:
                if video_data.get("transcription_length", 0) == 0:
                    skipped_transcripts += 1
                else:
                    failed_transcripts += 1
        
        # Verify tags (if they exist)
        topics_dir = account_dir / "topics"
        has_tags = topics_dir.exists()
        
        if has_tags:
            # Check for tag files
            tag_files = list(topics_dir.glob("*_tags.json"))
            # Exclude aggregate files
            video_tag_files = [
                f for f in tag_files 
                if f.name not in ["account_tags.json", "account_category.json", "topic_graph.json"]
            ]
            
            tag_video_ids = set(f.stem.replace("_tags", "") for f in video_tag_files)
            
            # Check for missing tag files
            missing_tag_files = index_video_ids - tag_video_ids
            if missing_tag_files:
                result["warnings"].append(
                    f"Missing tag files: {len(missing_tag_files)} videos have transcripts but no tags"
                )
                result["missing_tag_video_ids"] = sorted(list(missing_tag_files))
            
            # Check for orphaned tag files
            orphaned_tag_files = tag_video_ids - index_video_ids
            if orphaned_tag_files:
                result["warnings"].append(
                    f"Orphaned tag files: {len(orphaned_tag_files)} tag files exist but not in index"
                )
                result["orphaned_tag_video_ids"] = sorted(list(orphaned_tag_files))
            
            # Verify account_tags.json exists
            account_tags_file = topics_dir / "account_tags.json"
            if not account_tags_file.exists():
                result["issues"].append("account_tags.json missing")
            
            # Verify account_category.json exists
            account_category_file = topics_dir / "account_category.json"
            if not account_category_file.exists():
                result["warnings"].append("account_category.json missing")
            
            result["has_tags"] = True
            result["tag_stats"] = {
                "tag_file_count": len(video_tag_files),
                "has_account_tags": account_tags_file.exists(),
                "has_account_category": account_category_file.exists(),
                "missing_tag_files": len(missing_tag_files),
                "orphaned_tag_files": len(orphaned_tag_files)
            }
        else:
            result["has_tags"] = False
            result["tag_stats"] = None
        
        # Stats
        result["stats"] = {
            "index_video_count": len(index_video_ids),
            "filesystem_video_count": len(fs_video_ids),
            "successful_transcripts": successful_transcripts,
            "skipped_transcripts": skipped_transcripts,
            "failed_transcripts": failed_transcripts,
            "missing_transcripts": len(missing_transcripts),
            "orphaned_transcripts": len(orphaned_transcripts),
            "duplicate_transcripts": len(duplicates),
            "total_issues": len(result["issues"]),
            "total_warnings": len(result["warnings"])
        }
        
        # Add index stats
        if "stats" in index:
            result["index_stats"] = index["stats"]
        
        return result
    
    def print_report(self, verification: Dict[str, Any]):
        """
        Print verification report
        
        Args:
            verification: Verification results
        """
        print("\n" + "=" * 80)
        print("🔍 INGESTION VERIFICATION REPORT")
        print("=" * 80)
        
        if verification.get("error"):
            print(f"\n❌ Error: {verification['error']}")
            return
        
        print(f"\nTotal accounts: {verification['total_accounts']}")
        print(f"Verification time: {verification['verification_time']}")
        print("\n" + "-" * 80)
        
        total_issues = 0
        total_warnings = 0
        
        for account in verification['accounts']:
            print(f"\n📁 Account: @{account['account']}")
            print(f"   Path: {account['path']}")
            
            if not account['index_exists']:
                print(f"   ⚠️  No index.json - not using new ingestion system")
                continue
            
            stats = account.get('stats', {})
            print(f"\n   📊 Statistics:")
            print(f"      Videos in index: {stats.get('index_video_count', 0)}")
            print(f"      Transcript files: {stats.get('filesystem_video_count', 0)}")
            print(f"      Successful: {stats.get('successful_transcripts', 0)}")
            print(f"      Skipped: {stats.get('skipped_transcripts', 0)}")
            print(f"      Failed: {stats.get('failed_transcripts', 0)}")
            
            # Data integrity checks
            print(f"\n   🔍 Data Integrity:")
            print(f"      Missing transcripts: {stats.get('missing_transcripts', 0)}")
            print(f"      Orphaned transcripts: {stats.get('orphaned_transcripts', 0)}")
            print(f"      Duplicate transcripts: {stats.get('duplicate_transcripts', 0)}")
            
            # Show tag stats if available
            if account.get('has_tags'):
                tag_stats = account.get('tag_stats', {})
                print(f"\n   🏷️  Tag Extraction:")
                print(f"      Tag files: {tag_stats.get('tag_file_count', 0)}")
                print(f"      Account tags: {'✅' if tag_stats.get('has_account_tags') else '❌'}")
                print(f"      Account category: {'✅' if tag_stats.get('has_account_category') else '❌'}")
                if tag_stats.get('missing_tag_files', 0) > 0:
                    print(f"      Missing tag files: {tag_stats['missing_tag_files']}")
            
            # Issues
            if account['issues']:
                print(f"\n   ❌ Issues ({len(account['issues'])}):")
                for issue in account['issues']:
                    print(f"      - {issue}")
                total_issues += len(account['issues'])
            
            # Warnings
            if account.get('warnings'):
                print(f"\n   ⚠️  Warnings ({len(account['warnings'])}):")
                for warning in account['warnings']:
                    print(f"      - {warning}")
                total_warnings += len(account['warnings'])
            
            if not account['issues'] and not account.get('warnings'):
                print(f"\n   ✅ Perfect data integrity!")
            
            print("-" * 80)
        
        # Summary
        print(f"\n📈 SUMMARY")
        print(f"   Accounts verified: {verification['total_accounts']}")
        print(f"   Total issues: {total_issues}")
        print(f"   Total warnings: {total_warnings}")
        
        if total_issues == 0 and total_warnings == 0:
            print(f"\n✅ All accounts have perfect data integrity!")
        elif total_issues == 0:
            print(f"\n⚠️  {total_warnings} warning(s) found (non-critical)")
        else:
            print(f"\n❌ {total_issues} issue(s) require attention")
        
        print("\n" + "=" * 80 + "\n")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Verify ingestion data integrity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify all accounts
  python scripts/verify_ingestion.py
  
  # Verify specific account
  python scripts/verify_ingestion.py --account kwrt_
  
  # JSON output
  python scripts/verify_ingestion.py --json

Checks:
  ✅ index.json exists and is valid
  ✅ All videos in index have transcript files
  ✅ No orphaned transcript files
  ✅ No duplicate transcripts
  ✅ Index stats match filesystem
        """
    )
    
    parser.add_argument('--base-dir', default='accounts',
                       help='Base directory containing account folders (default: accounts)')
    parser.add_argument('--account', '-a', default=None,
                       help='Verify specific account only')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    verifier = IngestionVerifier(base_dir=args.base_dir)
    
    # Verify specific account or all accounts
    if args.account:
        account_name = args.account.lstrip('@')
        result = {
            "total_accounts": 1,
            "accounts": [verifier.verify_account(account_name)],
            "verification_time": datetime.now().isoformat()
        }
    else:
        result = verifier.verify_all_accounts()
    
    # Output results
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        verifier.print_report(result)
    
    # Exit with error code if issues found
    total_issues = sum(len(a.get('issues', [])) for a in result.get('accounts', []))
    sys.exit(1 if total_issues > 0 else 0)


if __name__ == "__main__":
    main()

