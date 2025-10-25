#!/usr/bin/env python3
"""
Semantic Search Storage - FAISS index and metadata storage
Handles FAISS index persistence and embedding metadata management
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import faiss
from datetime import datetime


class FAISSStorage:
    """FAISS index storage for semantic search"""
    
    def __init__(self, index_path: str = "data/search/index.faiss", metadata_path: str = "data/search/embeddings.jsonl"):
        """
        Initialize FAISS storage
        
        Args:
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSONL file
        """
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize index
        self.index = None
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        self.metadata = []
        self.load_index()
    
    def load_index(self):
        """Load existing FAISS index and metadata"""
        try:
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                self.logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                self.logger.info("Created new FAISS index")
            
            # Load metadata
            if self.metadata_path.exists():
                self.metadata = []
                with open(self.metadata_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            self.metadata.append(json.loads(line))
                self.logger.info(f"Loaded {len(self.metadata)} metadata entries")
            
        except Exception as e:
            self.logger.error(f"Error loading index: {e}")
            # Create fresh index
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []
    
    def add_embeddings(self, embedded_segments: List[Dict[str, Any]]) -> bool:
        """
        Add embeddings to FAISS index
        
        Args:
            embedded_segments: List of segments with embeddings
            
        Returns:
            Success status
        """
        if not embedded_segments:
            return True
        
        try:
            # Extract embeddings and metadata
            embeddings = []
            new_metadata = []
            
            for segment in embedded_segments:
                embedding = np.array(segment["embedding"], dtype=np.float32)
                embeddings.append(embedding)
                
                # Create metadata entry
                metadata_entry = {
                    "video_id": segment["video_id"],
                    "username": segment["username"],
                    "segment_id": segment["segment_id"],
                    "text": segment["text"],
                    "length": segment["length"],
                    "timestamp": segment.get("timestamp"),
                    "start_time": segment.get("start_time"),
                    "end_time": segment.get("end_time"),
                    "sentence_index": segment.get("sentence_index"),
                    "added_at": datetime.now().isoformat()
                }
                new_metadata.append(metadata_entry)
            
            # Convert to numpy array
            embeddings_array = np.vstack(embeddings)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings_array)
            
            # Add to index
            self.index.add(embeddings_array)
            
            # Add metadata
            self.metadata.extend(new_metadata)
            
            self.logger.info(f"Added {len(embeddings)} embeddings to index")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding embeddings: {e}")
            return False
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        if self.index.ntotal == 0:
            return []
        
        try:
            # Normalize query embedding
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
            
            # Build results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.metadata):
                    result = self.metadata[idx].copy()
                    result["score"] = float(score)
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching index: {e}")
            return []
    
    def save_index(self) -> bool:
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            with open(self.metadata_path, 'w') as f:
                for entry in self.metadata:
                    f.write(json.dumps(entry) + '\n')
            
            self.logger.info(f"Saved index with {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving index: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "metadata_entries": len(self.metadata),
            "index_path": str(self.index_path),
            "metadata_path": str(self.metadata_path)
        }
    
    def clear_index(self):
        """Clear all embeddings and metadata"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        self.logger.info("Cleared index")


class EmbeddingManager:
    """Manage embedding storage and retrieval"""
    
    def __init__(self, index_path: str = "data/search/index.faiss", metadata_path: str = "data/search/embeddings.jsonl"):
        """
        Initialize embedding manager
        
        Args:
            index_path: Path to FAISS index
            metadata_path: Path to metadata file
        """
        self.storage = FAISSStorage(index_path, metadata_path)
        self.logger = logging.getLogger(__name__)
    
    def add_transcript_segments(self, embedded_segments: List[Dict[str, Any]]) -> bool:
        """
        Add transcript segments to search index
        
        Args:
            embedded_segments: List of embedded segments
            
        Returns:
            Success status
        """
        success = self.storage.add_embeddings(embedded_segments)
        if success:
            self.storage.save_index()
        return success
    
    def search_semantic(self, query: str, model, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search
        
        Args:
            query: Search query
            model: Sentence transformer model
            top_k: Number of results
            
        Returns:
            Search results
        """
        try:
            # Generate query embedding
            query_embedding = model.encode([query], convert_to_numpy=True)[0]
            
            # Search index
            results = self.storage.search(query_embedding, top_k)
            
            self.logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return self.storage.get_stats()
    
    def clear_all(self):
        """Clear all embeddings"""
        self.storage.clear_index()
        self.storage.save_index()
