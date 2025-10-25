#!/usr/bin/env python3
"""
Timestamp Extractor - Extract sentence-level timestamps from transcripts
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class TimestampExtractor:
    """Extract timestamps and sentence positions from transcripts"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_sentence_timestamps(self, transcript: str, video_duration: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Extract sentence-level timestamps from transcript
        
        Args:
            transcript: Full transcript text
            video_duration: Video duration in seconds (optional)
            
        Returns:
            List of sentences with estimated timestamps
        """
        if not transcript or len(transcript.strip()) < 50:
            return []
        
        # Split into sentences
        sentences = self._split_into_sentences(transcript)
        
        # Calculate estimated timestamps
        if video_duration:
            timestamps = self._calculate_timestamps_with_duration(sentences, video_duration)
        else:
            timestamps = self._estimate_timestamps_by_length(sentences)
        
        return timestamps
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Clean text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _calculate_timestamps_with_duration(self, sentences: List[str], duration: float) -> List[Dict[str, Any]]:
        """Calculate timestamps using video duration"""
        if not sentences:
            return []
        
        # Calculate total character count
        total_chars = sum(len(s) for s in sentences)
        
        results = []
        current_time = 0.0
        
        for i, sentence in enumerate(sentences):
            # Estimate time based on character proportion
            sentence_ratio = len(sentence) / total_chars
            sentence_duration = sentence_ratio * duration
            
            results.append({
                "sentence": sentence,
                "start_time": current_time,
                "end_time": current_time + sentence_duration,
                "duration": sentence_duration,
                "sentence_index": i
            })
            
            current_time += sentence_duration
        
        return results
    
    def _estimate_timestamps_by_length(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Estimate timestamps based on text length (fallback method)"""
        if not sentences:
            return []
        
        # Assume average speaking rate of 150 words per minute
        words_per_second = 150 / 60  # 2.5 words per second
        
        results = []
        current_time = 0.0
        
        for i, sentence in enumerate(sentences):
            # Count words in sentence
            word_count = len(sentence.split())
            sentence_duration = word_count / words_per_second
            
            results.append({
                "sentence": sentence,
                "start_time": current_time,
                "end_time": current_time + sentence_duration,
                "duration": sentence_duration,
                "sentence_index": i
            })
            
            current_time += sentence_duration
        
        return results
    
    def find_sentence_in_segment(self, segment_text: str, sentences: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find which sentence a segment belongs to
        
        Args:
            segment_text: Text segment to find
            sentences: List of sentences with timestamps
            
        Returns:
            Sentence metadata if found
        """
        # Clean segment text
        segment_clean = re.sub(r'\s+', ' ', segment_text.strip())
        
        for sentence_data in sentences:
            sentence_clean = re.sub(r'\s+', ' ', sentence_data["sentence"].strip())
            
            # Check if segment is contained in sentence or vice versa
            if (segment_clean in sentence_clean or 
                sentence_clean in segment_clean or
                self._text_similarity(segment_clean, sentence_clean) > 0.7):
                return sentence_data
        
        return None
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (simple word overlap)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_context_sentences(self, sentences: List[Dict[str, Any]], target_sentence: Dict[str, Any], context_size: int = 3) -> List[Dict[str, Any]]:
        """
        Get context sentences around a target sentence
        
        Args:
            sentences: All sentences with timestamps
            target_sentence: Target sentence to get context for
            context_size: Number of sentences before/after
            
        Returns:
            List of context sentences
        """
        target_index = target_sentence.get("sentence_index", 0)
        
        start_idx = max(0, target_index - context_size)
        end_idx = min(len(sentences), target_index + context_size + 1)
        
        return sentences[start_idx:end_idx]
