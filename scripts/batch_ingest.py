#!/usr/bin/env python3
"""
Batch Ingestion Script - Process multiple TikTok accounts
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("⚠️  Install tqdm for progress bars: pip install tqdm")

from scripts.ingest_account import IdempotentIngestionManager


class BatchIngestionManager:
    """Manage batch ingestion of multiple accounts"""
    
    def __init__(self, 
                 accounts: List[str],
                 base_dir: str = "accounts",
                 max_videos: int = None,
                 model_size: str = "small",
                 cookies_file: str = None,
                 min_speech_threshold: int = 50,
                 verbose: bool = False):
        """
        Initialize batch ingestion manager
        
        Args:
            accounts: List of TikTok usernames
            base_dir: Base directory for accounts
            max_videos: Maximum videos per account
            model_size: Whisper model size
            cookies_file: Path to cookies.txt
            min_speech_threshold: Minimum speech characters
            verbose: Verbose logging
        """
        self.accounts = [a.lstrip('@') for a in accounts]
        self.base_dir = base_dir
        self.max_videos = max_videos
        self.model_size = model_size
        self.cookies_file = cookies_file
        self.min_speech_threshold = min_speech_threshold
        self.verbose = verbose
        
        self.results = []
    
    def process_all(self) -> Dict[str, Any]:
        """Process all accounts"""
        start_time = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"📦 BATCH INGESTION")
        print(f"{'='*80}")
        print(f"Accounts to process: {len(self.accounts)}")
        print(f"Max videos per account: {self.max_videos or '10 (default)'}")
        print(f"Model size: {self.model_size}")
        print(f"{'='*80}\n")
        
        # Create iterator with or without progress bar
        if HAS_TQDM:
            account_iter = tqdm(self.accounts, desc="Accounts", unit="account")
        else:
            account_iter = self.accounts
        
        for i, username in enumerate(account_iter, 1):
            if not HAS_TQDM:
                print(f"\n[{i}/{len(self.accounts)}] Processing @{username}...")
            
            try:
                manager = IdempotentIngestionManager(username, self.base_dir)
                result = manager.ingest_account(
                    max_videos=self.max_videos,
                    model_size=self.model_size,
                    cookies_file=self.cookies_file,
                    min_speech_threshold=self.min_speech_threshold,
                    verbose=self.verbose
                )
                result["account"] = username
                self.results.append(result)
                
            except Exception as e:
                print(f"❌ Error processing @{username}: {e}")
                self.results.append({
                    "account": username,
                    "error": str(e),
                    "success": False
                })
        
        # Calculate totals
        total_duration = (datetime.now() - start_time).total_seconds()
        
        # Print summary
        self.print_summary(total_duration)
        
        # Export CSV if available
        self.export_csv()
        
        return {
            "total_accounts": len(self.accounts),
            "results": self.results,
            "total_duration": total_duration,
            "batch_time": datetime.now().isoformat()
        }
    
    def print_summary(self, total_duration: float):
        """Print batch summary"""
        print(f"\n{'='*80}")
        print(f"📊 BATCH INGESTION SUMMARY")
        print(f"{'='*80}\n")
        
        total_videos = 0
        total_processed = 0
        total_skipped = 0
        total_failed = 0
        successful_accounts = 0
        
        for result in self.results:
            if not result.get("error"):
                total_videos += result.get("all_videos", 0)
                total_processed += result.get("newly_processed", 0)
                total_skipped += result.get("newly_skipped", 0)
                total_failed += result.get("newly_failed", 0)
                if result.get("newly_processed", 0) > 0:
                    successful_accounts += 1
        
        print(f"✅ Accounts processed: {len(self.results)}")
        print(f"✅ Accounts with new videos: {successful_accounts}")
        print(f"✅ Total videos found: {total_videos}")
        print(f"✅ Newly transcribed: {total_processed}")
        print(f"⏭️  Skipped (no speech): {total_skipped}")
        print(f"❌ Failed: {total_failed}")
        print(f"⏱️  Total time: {total_duration:.0f}s ({total_duration/60:.1f}m)")
        
        print(f"\n{'='*80}")
        print(f"Per-Account Details:")
        print(f"{'='*80}\n")
        
        for result in self.results:
            account = result.get("account", "Unknown")
            if result.get("error"):
                print(f"  ❌ @{account}: {result['error']}")
            else:
                processed = result.get("newly_processed", 0)
                already = result.get("already_processed", 0)
                print(f"  ✅ @{account}: {processed} new, {already} already processed")
        
        print(f"\n{'='*80}\n")
    
    def export_csv(self):
        """Export results to CSV"""
        try:
            import csv
            
            output_dir = Path(self.base_dir) / "_batch_reports"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = output_dir / f"batch_ingestion_{timestamp}.csv"
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'account', 'all_videos', 'already_processed', 
                    'newly_processed', 'newly_skipped', 'newly_failed',
                    'duration', 'status'
                ])
                writer.writeheader()
                
                for result in self.results:
                    writer.writerow({
                        'account': result.get('account', ''),
                        'all_videos': result.get('all_videos', 0),
                        'already_processed': result.get('already_processed', 0),
                        'newly_processed': result.get('newly_processed', 0),
                        'newly_skipped': result.get('newly_skipped', 0),
                        'newly_failed': result.get('newly_failed', 0),
                        'duration': f"{result.get('duration', 0):.1f}s",
                        'status': 'error' if result.get('error') else 'success'
                    })
            
            print(f"📄 CSV report exported: {csv_file}\n")
            
        except Exception as e:
            print(f"⚠️  Failed to export CSV: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Batch ingestion for multiple TikTok accounts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process multiple accounts
  python scripts/batch_ingest.py --users kwrt_ matrix.v5 beabettermandaily
  
  # From file
  python scripts/batch_ingest.py --file accounts.txt
  
  # With options
  python scripts/batch_ingest.py --users kwrt_ matrix.v5 --max-videos 50 --model-size medium
  
  # accounts.txt format (one username per line):
  kwrt_
  matrix.v5
  beabettermandaily

Features:
  - ✅ Process multiple accounts in one run
  - ✅ Progress bars (if tqdm installed)
  - ✅ CSV export of results
  - ✅ Idempotent per account
  - ✅ Continues on errors
        """
    )
    
    # Account input
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--users', '-u', nargs='+',
                            help='List of TikTok usernames')
    input_group.add_argument('--file', '-f',
                            help='File containing usernames (one per line)')
    
    # Options
    parser.add_argument('--base-dir', default='accounts',
                       help='Base directory for accounts (default: accounts)')
    parser.add_argument('--max-videos', type=int, default=None,
                       help='Maximum videos per account (default: 10 or from env)')
    parser.add_argument('--model-size', default='small',
                       choices=['tiny', 'small', 'medium', 'large'],
                       help='Whisper model size (default: small)')
    parser.add_argument('--cookies', dest='cookies_file', default=None,
                       help='Path to cookies.txt for authenticated scraping')
    parser.add_argument('--min-speech', type=int, default=50,
                       help='Minimum characters for speech detection (default: 50)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Get list of accounts
    if args.users:
        accounts = args.users
    else:
        # Read from file
        try:
            with open(args.file, 'r') as f:
                accounts = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except Exception as e:
            print(f"❌ Error reading file {args.file}: {e}")
            sys.exit(1)
    
    if not accounts:
        print("❌ No accounts specified")
        sys.exit(1)
    
    # Run batch ingestion
    manager = BatchIngestionManager(
        accounts=accounts,
        base_dir=args.base_dir,
        max_videos=args.max_videos,
        model_size=args.model_size,
        cookies_file=args.cookies_file,
        min_speech_threshold=args.min_speech,
        verbose=args.verbose
    )
    
    results = manager.process_all()
    
    # Exit with appropriate code
    errors = sum(1 for r in results['results'] if r.get('error'))
    sys.exit(1 if errors > 0 else 0)


if __name__ == "__main__":
    main()


