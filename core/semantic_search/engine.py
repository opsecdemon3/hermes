#!/usr/bin/env python3
"""
Semantic Search Engine - Main search functionality
Coordinates embedding generation, storage, and search operations
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from .embedder import SegmentProcessor
from .storage import EmbeddingManager


class SemanticSearchEngine:
    """Main semantic search engine"""
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 index_path: str = "data/search/index.faiss",
                 metadata_path: str = "data/search/embeddings.jsonl"):
        """
        Initialize semantic search engine
        
        Args:
            model_name: Sentence transformer model
            index_path: FAISS index path
            metadata_path: Metadata file path
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.segment_processor = SegmentProcessor(model_name)
        self.embedding_manager = EmbeddingManager(index_path, metadata_path)
        
        # Load model for search
        self.logger.info(f"Loading search model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        self.logger.info("Semantic search engine initialized")
    
    def process_transcript(self, transcript: str, video_id: str, username: str) -> bool:
        """
        Process a transcript and add to search index
        
        Args:
            transcript: Full transcript text
            video_id: Video identifier
            username: Account username
            
        Returns:
            Success status
        """
        try:
            # Process transcript into embedded segments
            embedded_segments = self.segment_processor.process_transcript(
                transcript, video_id, username
            )
            
            if not embedded_segments:
                self.logger.warning(f"No segments created for {video_id}")
                return False
            
            # Add to search index
            success = self.embedding_manager.add_transcript_segments(embedded_segments)
            
            if success:
                self.logger.info(f"Successfully processed {len(embedded_segments)} segments for {video_id}")
            else:
                self.logger.error(f"Failed to add segments for {video_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error processing transcript {video_id}: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search with enhanced provenance
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results with provenance
        """
        try:
            results = self.embedding_manager.search_semantic(query, self.model, top_k)
            
            # Format results with enhanced provenance
            formatted_results = []
            for result in results:
                # Create snippet (2-3 sentences)
                snippet = self._create_snippet(result["text"])
                
                # Format timestamp
                timestamp_str = self._format_timestamp(result.get("start_time"))
                
                formatted_results.append({
                    "text": result["text"],  # Full segment text
                    "snippet": snippet,      # Short snippet for display
                    "video_id": result["video_id"],
                    "username": result["username"],
                    "timestamp": timestamp_str,
                    "start_time": result.get("start_time"),
                    "end_time": result.get("end_time"),
                    "score": result["score"],
                    "segment_id": result["segment_id"]
                })
            
            self.logger.info(f"Search '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error in search: {e}")
            return []
    
    def _create_snippet(self, text: str, max_sentences: int = 3) -> str:
        """Create a snippet from text (2-3 sentences)"""
        sentences = text.split('. ')
        if len(sentences) <= max_sentences:
            return text
        
        snippet_sentences = sentences[:max_sentences]
        snippet = '. '.join(snippet_sentences)
        if not snippet.endswith('.'):
            snippet += '.'
        
        return snippet
    
    def _format_timestamp(self, start_time: Optional[float]) -> str:
        """Format timestamp as MM:SS"""
        if start_time is None:
            return "00:00"
        
        minutes = int(start_time // 60)
        seconds = int(start_time % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return self.embedding_manager.get_stats()
    
    def clear_index(self):
        """Clear all search data"""
        self.embedding_manager.clear_all()
        self.logger.info("Cleared search index")


class TranscriptIndexer:
    """Index transcripts from existing accounts"""
    
    def __init__(self, base_dir: str = "accounts"):
        """
        Initialize transcript indexer
        
        Args:
            base_dir: Base directory containing accounts
        """
        self.base_dir = Path(base_dir)
        self.search_engine = SemanticSearchEngine()
        self.logger = logging.getLogger(__name__)
    
    def index_account(self, username: str) -> Dict[str, Any]:
        """
        Index all transcripts for an account
        
        Args:
            username: Account username
            
        Returns:
            Indexing results
        """
        account_dir = self.base_dir / username
        transcriptions_dir = account_dir / "transcriptions"
        index_file = account_dir / "index.json"
        
        results = {
            "username": username,
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "total_segments": 0
        }
        
        if not transcriptions_dir.exists():
            self.logger.warning(f"No transcriptions directory for {username}")
            return results
        
        # Load account index to get video metadata
        video_metadata = {}
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
                    video_metadata = index_data.get("processed_videos", {})
            except Exception as e:
                self.logger.warning(f"Could not load index for {username}: {e}")
        
        # Process each transcript
        for transcript_file in transcriptions_dir.glob("*_transcript.txt"):
            video_id = transcript_file.stem.replace("_transcript", "")
            
            try:
                # Read transcript
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_content = f.read()
                
                # Extract transcript text (skip header)
                if "=" * 50 in transcript_content:
                    transcript_text = transcript_content.split("=" * 50, 1)[1].strip()
                else:
                    transcript_text = transcript_content
                
                if not transcript_text or len(transcript_text) < 50:
                    results["skipped"] += 1
                    continue
                
                # Process transcript
                success = self.search_engine.process_transcript(
                    transcript_text, video_id, username
                )
                
                if success:
                    results["processed"] += 1
                    # Count segments (approximate)
                    segments = len(transcript_text) // 200  # Rough estimate
                    results["total_segments"] += segments
                else:
                    results["failed"] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {transcript_file}: {e}")
                results["failed"] += 1
        
        self.logger.info(f"Indexed {username}: {results}")
        return results
    
    def index_all_accounts(self) -> Dict[str, Any]:
        """
        Index all accounts in the base directory
        
        Returns:
            Overall indexing results
        """
        results = {
            "accounts": [],
            "total_processed": 0,
            "total_skipped": 0,
            "total_failed": 0,
            "total_segments": 0
        }
        
        for account_dir in self.base_dir.iterdir():
            if account_dir.is_dir() and not account_dir.name.startswith('.'):
                account_results = self.index_account(account_dir.name)
                results["accounts"].append(account_results)
                results["total_processed"] += account_results["processed"]
                results["total_skipped"] += account_results["skipped"]
                results["total_failed"] += account_results["failed"]
                results["total_segments"] += account_results["total_segments"]
        
        self.logger.info(f"Indexed all accounts: {results}")
        return results
