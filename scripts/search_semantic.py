#!/usr/bin/env python3
"""
Semantic Search CLI - Search transcripts using semantic similarity
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.semantic_search.engine import SemanticSearchEngine, TranscriptIndexer


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Semantic search over TikTok transcripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for meaning-related content
  python scripts/search_semantic.py "meaning of life"
  
  # Search with more results
  python scripts/search_semantic.py "philosophy" --top-k 10
  
  # Index all accounts first
  python scripts/search_semantic.py --index-all
  
  # Index specific account
  python scripts/search_semantic.py --index-account kwrt_
  
  # Show search stats
  python scripts/search_semantic.py --stats

How it works:
  1. Transcripts are segmented into searchable chunks
  2. Each segment gets a semantic embedding
  3. FAISS index enables fast similarity search
  4. Results include video ID, username, and text snippet
        """
    )
    
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results to return')
    parser.add_argument('--index-all', action='store_true', help='Index all accounts')
    parser.add_argument('--index-account', help='Index specific account')
    parser.add_argument('--stats', action='store_true', help='Show search index statistics')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print(f"\n{'='*80}")
    print(f"🔍 SEMANTIC SEARCH")
    print(f"{'='*80}\n")
    
    try:
        # Initialize search engine
        search_engine = SemanticSearchEngine()
        
        # Handle different commands
        if args.stats:
            show_stats(search_engine)
        elif args.index_all:
            index_all_accounts()
        elif args.index_account:
            index_account(args.index_account)
        elif args.query:
            search_query(search_engine, args.query, args.top_k)
        else:
            print("❌ Please provide a search query or use --help for options")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def show_stats(search_engine):
    """Show search index statistics"""
    stats = search_engine.get_stats()
    
    print("📊 Search Index Statistics:")
    print(f"   Total vectors: {stats['total_vectors']}")
    print(f"   Dimension: {stats['dimension']}")
    print(f"   Metadata entries: {stats['metadata_entries']}")
    print(f"   Index path: {stats['index_path']}")
    print(f"   Metadata path: {stats['metadata_path']}")
    
    if stats['total_vectors'] == 0:
        print("\n⚠️  No embeddings found. Run --index-all first.")


def index_all_accounts():
    """Index all accounts"""
    print("📚 Indexing all accounts...")
    
    indexer = TranscriptIndexer()
    results = indexer.index_all_accounts()
    
    print(f"\n📊 Indexing Results:")
    print(f"   Accounts processed: {len(results['accounts'])}")
    print(f"   Total segments: {results['total_segments']}")
    print(f"   Processed: {results['total_processed']}")
    print(f"   Skipped: {results['total_skipped']}")
    print(f"   Failed: {results['total_failed']}")
    
    for account in results['accounts']:
        if account['processed'] > 0:
            print(f"   ✅ {account['username']}: {account['processed']} transcripts, {account['total_segments']} segments")


def index_account(username):
    """Index specific account"""
    print(f"📚 Indexing account: {username}")
    
    indexer = TranscriptIndexer()
    results = indexer.index_account(username)
    
    print(f"\n📊 Results for @{username}:")
    print(f"   Processed: {results['processed']}")
    print(f"   Skipped: {results['skipped']}")
    print(f"   Failed: {results['failed']}")
    print(f"   Total segments: {results['total_segments']}")


def search_query(search_engine, query, top_k):
    """Perform semantic search with enhanced provenance"""
    print(f"🔍 Searching: '{query}'")
    print(f"📊 Top {top_k} results:\n")
    
    results = search_engine.search(query, top_k)
    
    if not results:
        print("❌ No results found. Try indexing accounts first with --index-all")
        return
    
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['score']:.3f}")
        print(f"   👤 @{result['username']} — 📹 {result['video_id']} — ⏰ {result['timestamp']}")
        print(f"   📝 Snippet: {result['snippet']}")
        print(f"   🔗 Full context: python scripts/show_transcript.py --video {result['video_id']} --username {result['username']} --jump {result['timestamp']}")
        print()
    
    print(f"✅ Found {len(results)} results")


if __name__ == "__main__":
    main()
