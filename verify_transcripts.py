#!/usr/bin/env python3
"""
Verification script for TikTok transcription outputs
Checks folder structure and transcript counts for each account
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class TranscriptVerifier:
    """Verify transcription outputs for TikTok accounts"""
    
    def __init__(self, base_dir: str = "accounts"):
        """
        Initialize verifier
        
        Args:
            base_dir: Base directory containing account folders
        """
        self.base_dir = Path(base_dir)
        
    def verify_all_accounts(self) -> Dict[str, Any]:
        """
        Verify all accounts in the base directory
        
        Returns:
            Dictionary with verification results
        """
        if not self.base_dir.exists():
            return {
                "error": f"Base directory not found: {self.base_dir}",
                "accounts": []
            }
        
        accounts = []
        
        # Find all account directories
        for account_dir in self.base_dir.iterdir():
            if account_dir.is_dir() and not account_dir.name.startswith('.'):
                account_name = account_dir.name
                result = self.verify_account(account_name)
                accounts.append(result)
        
        # Sort by account name
        accounts.sort(key=lambda x: x['account'])
        
        return {
            "total_accounts": len(accounts),
            "accounts": accounts,
            "verification_time": datetime.now().isoformat()
        }
    
    def verify_account(self, account_name: str) -> Dict[str, Any]:
        """
        Verify a single account's transcription outputs
        
        Args:
            account_name: TikTok account username
            
        Returns:
            Verification result dictionary
        """
        account_path = self.base_dir / account_name
        transcriptions_path = account_path / "transcriptions"
        
        result = {
            "account": account_name,
            "path": str(account_path),
            "exists": account_path.exists(),
            "transcriptions_folder_exists": transcriptions_path.exists(),
            "transcript_count": 0,
            "results_file_exists": False,
            "results_data": None,
            "transcripts": [],
            "issues": []
        }
        
        if not account_path.exists():
            result["issues"].append("Account directory does not exist")
            return result
        
        if not transcriptions_path.exists():
            result["issues"].append("Transcriptions folder does not exist")
            return result
        
        # Check for results JSON file
        results_file = transcriptions_path / f"{account_name}_results.json"
        if results_file.exists():
            result["results_file_exists"] = True
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    results_data = json.load(f)
                    result["results_data"] = {
                        "stats": results_data.get("stats", {}),
                        "timestamp": results_data.get("timestamp"),
                        "processed_count": len(results_data.get("processed_videos", []))
                    }
            except Exception as e:
                result["issues"].append(f"Failed to read results file: {e}")
        else:
            result["issues"].append("Results JSON file not found")
        
        # Count transcript files
        transcript_files = list(transcriptions_path.glob("*_transcript.txt"))
        result["transcript_count"] = len(transcript_files)
        
        # Verify each transcript
        for transcript_file in sorted(transcript_files):
            video_id = transcript_file.stem.replace("_transcript", "")
            
            try:
                # Read transcript file
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract transcription (after the header separator)
                if "=" * 50 in content:
                    transcription = content.split("=" * 50, 1)[1].strip()
                else:
                    transcription = content
                
                transcript_info = {
                    "video_id": video_id,
                    "file": transcript_file.name,
                    "file_size": transcript_file.stat().st_size,
                    "char_count": len(transcription),
                    "line_count": len(content.splitlines()),
                    "has_content": len(transcription) > 50
                }
                
                result["transcripts"].append(transcript_info)
                
                # Check for issues
                if not transcript_info["has_content"]:
                    result["issues"].append(f"Video {video_id} has minimal content")
                
            except Exception as e:
                result["issues"].append(f"Failed to verify transcript {video_id}: {e}")
        
        # Cross-check results file with transcript files
        if result["results_file_exists"] and result["results_data"]:
            processed_count = result["results_data"]["processed_count"]
            if processed_count != result["transcript_count"]:
                result["issues"].append(
                    f"Mismatch: {processed_count} videos in results.json but {result['transcript_count']} transcript files"
                )
        
        return result
    
    def print_report(self, verification: Dict[str, Any]):
        """
        Print a formatted verification report
        
        Args:
            verification: Verification results dictionary
        """
        print("\n" + "=" * 80)
        print("📊 TRANSCRIPT VERIFICATION REPORT")
        print("=" * 80)
        
        if verification.get("error"):
            print(f"\n❌ Error: {verification['error']}")
            return
        
        print(f"\nTotal accounts: {verification['total_accounts']}")
        print(f"Verification time: {verification['verification_time']}")
        print("\n" + "-" * 80)
        
        for account in verification['accounts']:
            print(f"\n📁 Account: @{account['account']}")
            print(f"   Path: {account['path']}")
            print(f"   Transcripts: {account['transcript_count']}")
            
            if account['results_file_exists'] and account['results_data']:
                stats = account['results_data'].get('stats', {})
                print(f"   Processed: {stats.get('processed_videos', 0)}")
                print(f"   Skipped: {stats.get('skipped_videos', 0)}")
                print(f"   Failed: {stats.get('failed_videos', 0)}")
                print(f"   Processing time: {stats.get('processing_time', 0):.2f}s")
                print(f"   Last run: {account['results_data'].get('timestamp', 'Unknown')}")
            
            # Show transcript details
            if account['transcripts']:
                print(f"\n   Transcripts:")
                for t in account['transcripts']:
                    status = "✅" if t['has_content'] else "⚠️"
                    print(f"      {status} {t['video_id']}: {t['char_count']} chars")
            
            # Show issues
            if account['issues']:
                print(f"\n   ⚠️  Issues:")
                for issue in account['issues']:
                    print(f"      - {issue}")
            else:
                print(f"\n   ✅ No issues found")
            
            print("-" * 80)
        
        # Summary
        total_transcripts = sum(a['transcript_count'] for a in verification['accounts'])
        accounts_with_issues = sum(1 for a in verification['accounts'] if a['issues'])
        
        print(f"\n📈 SUMMARY")
        print(f"   Total accounts verified: {verification['total_accounts']}")
        print(f"   Total transcripts: {total_transcripts}")
        print(f"   Accounts with issues: {accounts_with_issues}")
        
        if accounts_with_issues == 0:
            print(f"\n✅ All accounts verified successfully!")
        else:
            print(f"\n⚠️  {accounts_with_issues} account(s) have issues")
        
        print("\n" + "=" * 80 + "\n")


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Verify TikTok transcription outputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python verify_transcripts.py
  python verify_transcripts.py --base-dir accounts
  python verify_transcripts.py --account kwrt_
        """
    )
    
    parser.add_argument('--base-dir', default='accounts', 
                       help='Base directory containing account folders (default: accounts)')
    parser.add_argument('--account', '-a', default=None,
                       help='Verify specific account only')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    verifier = TranscriptVerifier(base_dir=args.base_dir)
    
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
    has_issues = any(a.get('issues') for a in result.get('accounts', []))
    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()


