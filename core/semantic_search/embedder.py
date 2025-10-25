#!/usr/bin/env python3
"""
Semantic Search Embedder - Generate embeddings for transcript segments
Uses sentence-transformers for local, offline-first embedding generation
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import re

from .timestamp_extractor import TimestampExtractor


class TranscriptSegmenter:
    """Segment transcripts into searchable chunks"""
    
    def __init__(self, max_length: int = 200, overlap: int = 50):
        """
        Initialize segmenter
        
        Args:
            max_length: Maximum characters per segment
            overlap: Character overlap between segments
        """
        self.max_length = max_length
        self.overlap = overlap
        self.logger = logging.getLogger(__name__)
    
    def segment_transcript(self, transcript: str, video_id: str, username: str) -> List[Dict[str, Any]]:
        """
        Segment transcript into searchable chunks
        
        Args:
            transcript: Full transcript text
            video_id: Video identifier
            username: Account username
            
        Returns:
            List of segment dictionaries
        """
        if not transcript or len(transcript.strip()) < 50:
            return []
        
        # Clean transcript
        transcript = self._clean_transcript(transcript)
        
        # Split into sentences first
        sentences = self._split_into_sentences(transcript)
        
        segments = []
        current_segment = ""
        current_length = 0
        segment_id = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed max_length, save current segment
            if current_length + sentence_length > self.max_length and current_segment:
                segments.append(self._create_segment(
                    current_segment.strip(),
                    video_id,
                    username,
                    segment_id,
                    current_length
                ))
                
                # Start new segment with overlap
                overlap_text = self._get_overlap_text(current_segment)
                current_segment = overlap_text + " " + sentence
                current_length = len(current_segment)
                segment_id += 1
            else:
                current_segment += " " + sentence if current_segment else sentence
                current_length = len(current_segment)
        
        # Add final segment
        if current_segment.strip():
            segments.append(self._create_segment(
                current_segment.strip(),
                video_id,
                username,
                segment_id,
                current_length
            ))
        
        self.logger.debug(f"Created {len(segments)} segments for {video_id}")
        return segments
    
    def _clean_transcript(self, transcript: str) -> str:
        """Clean transcript text"""
        # Remove extra whitespace
        transcript = re.sub(r'\s+', ' ', transcript)
        # Remove special characters that might interfere with segmentation
        transcript = re.sub(r'[^\w\s.,!?;:\-]', '', transcript)
        return transcript.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting on common punctuation
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, segment: str) -> str:
        """Get overlap text from end of segment"""
        if len(segment) <= self.overlap:
            return segment
        return segment[-self.overlap:].strip()
    
    def _create_segment(self, text: str, video_id: str, username: str, segment_id: int, length: int) -> Dict[str, Any]:
        """Create segment dictionary"""
        return {
            "text": text,
            "video_id": video_id,
            "username": username,
            "segment_id": segment_id,
            "length": length,
            "timestamp": None  # Will be calculated if needed
        }


class EmbeddingGenerator:
    """Generate embeddings for transcript segments"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding generator
        
        Args:
            model_name: Sentence transformer model to use
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Loading embedding model: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            self.logger.info("Embedding model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embeddings(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for segments
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            List of segments with embeddings
        """
        if not segments:
            return []
        
        # Extract texts for batch embedding
        texts = [segment["text"] for segment in segments]
        
        try:
            # Generate embeddings in batch
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # Add embeddings to segments
            for i, segment in enumerate(segments):
                segment["embedding"] = embeddings[i].tolist()
            
            self.logger.info(f"Generated {len(embeddings)} embeddings")
            return segments
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
            return []


class SegmentProcessor:
    """Process transcript segments and generate embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", max_length: int = 200, overlap: int = 50):
        """
        Initialize segment processor
        
        Args:
            model_name: Sentence transformer model
            max_length: Maximum segment length
            overlap: Segment overlap
        """
        self.segmenter = TranscriptSegmenter(max_length, overlap)
        self.embedder = EmbeddingGenerator(model_name)
        self.timestamp_extractor = TimestampExtractor()
        self.logger = logging.getLogger(__name__)
    
    def process_transcript(self, transcript: str, video_id: str, username: str, video_duration: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Process transcript into embedded segments with timestamps
        
        Args:
            transcript: Full transcript text
            video_id: Video identifier
            username: Account username
            video_duration: Video duration in seconds (optional)
            
        Returns:
            List of embedded segments with timestamps
        """
        # Extract sentence-level timestamps
        sentence_timestamps = self.timestamp_extractor.extract_sentence_timestamps(transcript, video_duration)
        
        # Segment transcript
        segments = self.segmenter.segment_transcript(transcript, video_id, username)
        
        if not segments:
            self.logger.warning(f"No segments created for {video_id}")
            return []
        
        # Add timestamp information to segments
        for segment in segments:
            # Find which sentence this segment belongs to
            sentence_data = self.timestamp_extractor.find_sentence_in_segment(
                segment["text"], sentence_timestamps
            )
            
            if sentence_data:
                segment["start_time"] = sentence_data["start_time"]
                segment["end_time"] = sentence_data["end_time"]
                segment["sentence_index"] = sentence_data["sentence_index"]
            else:
                # Fallback: estimate timestamp based on segment position
                segment["start_time"] = None
                segment["end_time"] = None
                segment["sentence_index"] = None
        
        # Generate embeddings
        embedded_segments = self.embedder.generate_embeddings(segments)
        
        self.logger.info(f"Processed {len(embedded_segments)} segments for {video_id}")
        return embedded_segments
