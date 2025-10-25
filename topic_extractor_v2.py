#!/usr/bin/env python3
"""
Topic Extraction Engine V2 - Enhanced with quality guardrails, MMR, canonicalization, and time spans

Improvements:
- spaCy noun-phrase extraction for grammatical topics
- MMR (Maximal Marginal Relevance) for diversity
- Canonicalization with merge rules
- Timestamped evidence with confidence scores
- Stop-phrase filtering
- Umbrella clustering
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import Counter, defaultdict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
from dataclasses import dataclass, asdict
import re
from difflib import SequenceMatcher

# NLP imports
try:
    import spacy
    from sentence_transformers import SentenceTransformer
    from keybert import KeyBERT
    import nltk
    from nltk.corpus import stopwords
    HAS_NLP = True
except ImportError:
    HAS_NLP = False
    print("⚠️  NLP libraries not installed. Install with: pip install spacy sentence-transformers keybert nltk")


@dataclass
class TopicEvidence:
    """Evidence for a topic occurrence"""
    sentence_index: int
    start_time: float
    end_time: float
    text: str


@dataclass
class EnhancedTopic:
    """Enhanced topic with quality metrics"""
    tag: str
    canonical: str
    confidence: float
    sources: List[str]  # ["transcript", "title", "hashtag"]
    evidence: List[TopicEvidence]
    score: float
    type: str = "keyphrase"  # Topic type (default: keyphrase)
    source: str = "transcript"  # Primary source
    stats: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.stats is None:
            self.stats = {}
        if not self.source and self.sources:
            self.source = self.sources[0]


class TopicExtractorV2:
    """Enhanced topic extractor with quality guardrails"""
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 spacy_model: str = "en_core_web_sm",
                 config_dir: str = "config"):
        """
        Initialize enhanced topic extractor
        
        Args:
            model_name: Sentence transformer model
            spacy_model: spaCy model for NLP
            config_dir: Directory containing config files
        """
        if not HAS_NLP:
            raise ImportError("NLP libraries required")
        
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path(config_dir)
        
        # Load models
        self.logger.info(f"Loading models: {model_name}, {spacy_model}")
        self.st_model = SentenceTransformer(model_name)
        
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            self.logger.warning(f"spaCy model {spacy_model} not found. Downloading...")
            os.system(f"python -m spacy download {spacy_model}")
            self.nlp = spacy.load(spacy_model)
        
        # Load configurations
        self.stop_phrases = self._load_stop_phrases()
        self.canonical_map = self._load_canonical_map()
        
        self.logger.info("TopicExtractorV2 initialized")
    
    def _load_stop_phrases(self) -> Set[str]:
        """Load stop phrases from config"""
        stop_file = self.config_dir / "stop_phrases.txt"
        if not stop_file.exists():
            return set()
        
        stop_phrases = set()
        with open(stop_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    stop_phrases.add(line.lower())
        
        self.logger.info(f"Loaded {len(stop_phrases)} stop phrases")
        return stop_phrases
    
    def _load_canonical_map(self) -> Dict[str, Any]:
        """Load canonical topic mappings"""
        canon_file = self.config_dir / "canonical_topics.json"
        if not canon_file.exists():
            return {"merge_rules": {}, "auto_merge_threshold": {"cosine_similarity": 0.9, "edit_distance_max": 2}}
        
        with open(canon_file, 'r') as f:
            return json.load(f)
    
    def _extract_noun_phrases(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract noun phrases using spaCy
        
        Returns:
            List of (phrase, start_char, end_char) tuples
        """
        doc = self.nlp(text)
        noun_phrases = []
        
        for chunk in doc.noun_chunks:
            # Clean and lemmatize
            phrase = " ".join([token.lemma_.lower() for token in chunk if not token.is_stop])
            if phrase and len(phrase) > 2:
                noun_phrases.append((phrase, chunk.start_char, chunk.end_char))
        
        # Also extract proper nouns
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']:
                phrase = ent.text.lower()
                noun_phrases.append((phrase, ent.start_char, ent.end_char))
        
        return noun_phrases
    
    def _is_stop_phrase(self, phrase: str) -> bool:
        """Check if phrase matches stop phrases"""
        phrase_lower = phrase.lower().strip()
        return phrase_lower in self.stop_phrases
    
    def _canonicalize(self, phrase: str) -> str:
        """
        Map phrase to canonical form
        
        Returns:
            Canonical form of the phrase
        """
        phrase_lower = phrase.lower().strip()
        
        # Check merge rules
        merge_rules = self.canonical_map.get("merge_rules", {})
        if phrase_lower in merge_rules:
            return merge_rules[phrase_lower]
        
        return phrase_lower
    
    def _compute_mmr(self, 
                     candidates: List[str],
                     document_embedding: np.ndarray,
                     lambda_param: float = 0.7,
                     top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Maximal Marginal Relevance selection
        
        Formula: λ * relevance - (1-λ) * redundancy
        
        Args:
            candidates: List of candidate phrases
            document_embedding: Embedding of full document
            lambda_param: Balance between relevance and diversity (0-1)
            top_n: Number of topics to select
            
        Returns:
            List of (phrase, score) tuples
        """
        if not candidates:
            return []
        
        # Encode all candidates
        candidate_embeddings = self.st_model.encode(candidates)
        
        selected = []
        selected_embeddings = []
        remaining = list(range(len(candidates)))
        
        while len(selected) < min(top_n, len(candidates)):
            if not remaining:
                break
            
            mmr_scores = []
            for idx in remaining:
                # Relevance: similarity to document
                relevance = cosine_similarity(
                    candidate_embeddings[idx].reshape(1, -1),
                    document_embedding.reshape(1, -1)
                )[0][0]
                
                # Redundancy: max similarity to already selected
                if selected_embeddings:
                    redundancy = max([
                        cosine_similarity(
                            candidate_embeddings[idx].reshape(1, -1),
                            emb.reshape(1, -1)
                        )[0][0]
                        for emb in selected_embeddings
                    ])
                else:
                    redundancy = 0
                
                # MMR score
                mmr = lambda_param * relevance - (1 - lambda_param) * redundancy
                mmr_scores.append((idx, mmr))
            
            # Select best MMR score
            best_idx, best_score = max(mmr_scores, key=lambda x: x[1])
            selected.append((candidates[best_idx], float(best_score)))
            selected_embeddings.append(candidate_embeddings[best_idx])
            remaining.remove(best_idx)
        
        return selected
    
    def extract_video_topics_enhanced(self,
                                     transcript: str,
                                     sentence_timestamps: List[Dict[str, Any]],
                                     title: str = "",
                                     hashtags: List[str] = None,
                                     video_id: str = "",
                                     lambda_param: float = 0.7,
                                     max_topics: int = 10,
                                     min_confidence: float = 0.0) -> List[EnhancedTopic]:
        """
        Extract enhanced topics with evidence and timestamps
        
        Args:
            transcript: Full transcript text
            sentence_timestamps: List of sentence dicts with start/end times and text
            title: Video title
            hashtags: List of hashtags
            video_id: Video ID for logging
            lambda_param: MMR balance parameter (0-1)
            max_topics: Maximum topics to extract
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of EnhancedTopic objects
        """
        if not transcript or len(transcript) < 50:
            self.logger.warning(f"Transcript too short for {video_id}")
            return []
        
        hashtags = hashtags or []
        
        try:
            # Step 1: Extract noun phrase candidates
            noun_phrases = self._extract_noun_phrases(transcript)
            
            # Step 2: Filter stop phrases
            candidates = [phrase for phrase, _, _ in noun_phrases if not self._is_stop_phrase(phrase)]
            candidates = list(set(candidates))  # Deduplicate
            
            if not candidates:
                self.logger.warning(f"No valid candidates for {video_id}")
                return []
            
            # Step 3: Encode document
            doc_embedding = self.st_model.encode(transcript)
            
            # Step 4: MMR selection
            selected = self._compute_mmr(candidates, doc_embedding, lambda_param, max_topics * 2)
            
            # Step 5: Build enhanced topics with evidence
            enhanced_topics = []
            for phrase, mmr_score in selected:
                # Skip very low MMR scores (these are likely noise)
                if mmr_score < -0.1:
                    continue
                
                # Find evidence in transcript
                evidence = self._find_evidence(phrase, sentence_timestamps, transcript)
                # Note: Evidence is optional - topics can exist without sentence-level evidence
                
                # Canonicalize
                canonical = self._canonicalize(phrase)
                
                # Determine sources
                sources = ["transcript"]
                if title and phrase.lower() in title.lower():
                    sources.append("title")
                if any(phrase.lower() in tag.lower() for tag in hashtags):
                    sources.append("hashtag")
                
                # Compute confidence (normalized 0-1)
                confidence = self._compute_confidence(mmr_score, len(evidence))
                
                # Apply minimum confidence filter
                if confidence < min_confidence:
                    continue
                
                # Build enhanced topic
                topic = EnhancedTopic(
                    tag=phrase,
                    canonical=canonical,
                    confidence=confidence,
                    sources=sources,
                    evidence=evidence[:3],  # Keep top 3 evidence sentences
                    score=mmr_score,
                    type="keyphrase",
                    source=sources[0] if sources else "transcript",
                    stats={
                        "distinct_sentences": len(evidence),
                        "mmr_score": mmr_score
                    }
                )
                
                enhanced_topics.append(topic)
            
            # Sort by confidence
            enhanced_topics.sort(key=lambda x: x.confidence, reverse=True)
            
            return enhanced_topics[:max_topics]
            
        except Exception as e:
            self.logger.error(f"Error extracting topics for {video_id}: {e}", exc_info=True)
            return []
    
    def _find_evidence(self, phrase: str, sentence_timestamps: List[Dict[str, Any]], full_transcript: str = "") -> List[TopicEvidence]:
        """Find sentences containing the phrase"""
        evidence = []
        phrase_lower = phrase.lower()
        
        # Try with sentence_timestamps first if available
        if sentence_timestamps:
            for idx, sent in enumerate(sentence_timestamps):
                text = sent.get("text", sent.get("sentence", ""))
                if phrase_lower in text.lower():
                    ev = TopicEvidence(
                        sentence_index=idx,
                        start_time=sent.get("start_time", 0),
                        end_time=sent.get("end_time", 0),
                        text=text[:150]  # Truncate for storage
                    )
                    evidence.append(ev)
        
        # Fallback: search full transcript if no timestamps available
        elif full_transcript:
            sentences = [s.strip() for s in full_transcript.split('.') if s.strip()]
            for idx, sent in enumerate(sentences):
                if phrase_lower in sent.lower():
                    ev = TopicEvidence(
                        sentence_index=idx,
                        start_time=0.0,  # Unknown timestamp
                        end_time=0.0,
                        text=sent[:150]
                    )
                    evidence.append(ev)
                    if len(evidence) >= 5:  # Limit evidence collection
                        break
        
        return evidence
    
    def _compute_confidence(self, mmr_score: float, evidence_count: int) -> float:
        """
        Compute calibrated confidence score
        
        Factors:
        - MMR score (base relevance, typically -0.5 to 0.7 range)
        - Evidence count (more sentences = higher confidence)
        """
        # Normalize MMR score to 0-1 range
        # MMR typically ranges from -0.5 to 0.7, map to 0-1
        normalized_mmr = max(0, min(1.0, (mmr_score + 0.5) / 1.2))
        
        # Boost from evidence (log scale)
        evidence_boost = min(0.3, np.log1p(evidence_count) / 10)
        
        confidence = min(1.0, normalized_mmr + evidence_boost)
        return round(confidence, 3)
    
    def serialize_topics(self, topics: List[EnhancedTopic]) -> Dict[str, Any]:
        """Serialize enhanced topics to JSON-compatible dict"""
        return {
            "topics": [
                {
                    "tag": t.tag,
                    "canonical": t.canonical,
                    "confidence": t.confidence,
                    "sources": t.sources,
                    "evidence": [
                        {
                            "sentence_index": ev.sentence_index,
                            "start": ev.start_time,
                            "end": ev.end_time,
                            "text": ev.text
                        }
                        for ev in t.evidence
                    ],
                    "score": t.score,
                    "stats": t.stats
                }
                for t in topics
            ]
        }


    def extract_account_topics_v2(self, username: str, force: bool = False) -> Dict[str, Any]:
        """
        Extract V2 topics for all videos in an account
        
        Args:
            username: TikTok username
            force: Re-extract even if V2 tags exist
            
        Returns:
            Extraction summary
        """
        accounts_dir = Path("accounts")
        account_dir = accounts_dir / username
        
        if not account_dir.exists():
            raise FileNotFoundError(f"Account directory not found: {account_dir}")
        
        # Load index
        index_file = account_dir / "index.json"
        if not index_file.exists():
            raise FileNotFoundError(f"Index not found: {index_file}")
        
        with open(index_file, 'r') as f:
            index = json.load(f)
        
        processed_videos = index.get('processed_videos', {})
        topics_dir = account_dir / "topics"
        topics_dir.mkdir(exist_ok=True)
        transcriptions_dir = account_dir / "transcriptions"
        
        results = {
            "username": username,
            "total_videos": len(processed_videos),
            "extracted": 0,
            "skipped": 0,
            "failed": 0
        }
        
        self.logger.info(f"Extracting V2 topics for {len(processed_videos)} videos in @{username}...")
        
        for video_id, video_data in processed_videos.items():
            if not video_data.get('success'):
                results['skipped'] += 1
                continue
            
            # Check if V2 tags already exist
            v2_tag_file = topics_dir / f"{video_id}_tags_v2.json"
            if v2_tag_file.exists() and not force:
                self.logger.debug(f"V2 tags already exist for {video_id}, skipping")
                results['skipped'] += 1
                continue
            
            # Load transcript
            transcript_file = transcriptions_dir / f"{video_id}_transcript.txt"
            if not transcript_file.exists():
                self.logger.warning(f"Transcript not found for {video_id}")
                results['failed'] += 1
                continue
            
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    transcript_text = f.read().strip()
                
                if not transcript_text:
                    self.logger.warning(f"Empty transcript for {video_id}")
                    results['failed'] += 1
                    continue
                
                # Load timestamp data if available
                timestamp_file = transcriptions_dir / f"{video_id}_timestamps.json"
                timestamps = []
                if timestamp_file.exists():
                    with open(timestamp_file, 'r') as f:
                        timestamps = json.load(f)
                
                # Extract V2 topics
                title = video_data.get('title', '')
                hashtags = video_data.get('hashtags', [])
                
                topics = self.extract_video_topics_enhanced(
                    transcript_text,
                    timestamps,
                    title=title,
                    hashtags=hashtags
                )
                
                # Save V2 tags
                v2_data = {
                    "video_id": video_id,
                    "username": username,
                    "title": title,
                    "total_topics": len(topics),
                    "topics": [
                        {
                            "tag": t.tag,
                            "canonical": t.canonical,
                            "confidence": t.confidence,
                            "score": t.score,
                            "type": t.type,
                            "source": t.source,
                            "evidence": [
                                {
                                    "sentence_index": ev.sentence_index,
                                    "start": ev.start_time,
                                    "end": ev.end_time,
                                    "text": ev.text
                                }
                                for ev in t.evidence
                            ],
                            "stats": t.stats
                        }
                        for t in topics
                    ]
                }
                
                with open(v2_tag_file, 'w') as f:
                    json.dump(v2_data, f, indent=2)
                
                results['extracted'] += 1
                self.logger.debug(f"Extracted {len(topics)} V2 topics for {video_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to extract V2 topics for {video_id}: {e}")
                results['failed'] += 1
        
        self.logger.info(f"V2 extraction complete: {results['extracted']} extracted, {results['skipped']} skipped, {results['failed']} failed")
        return results


def main():
    """CLI for testing"""
    logging.basicConfig(level=logging.INFO)
    
    extractor = TopicExtractorV2()
    
    # Test transcript
    test_text = """
    Meditation isn't about stopping your thoughts. It's about observing them without judgment.
    When you practice mindfulness, you develop a deeper understanding of yourself and your patterns.
    Lucid dreaming takes this consciousness exploration to another level during sleep.
    """
    
    # Mock timestamps
    timestamps = [
        {"sentence": "Meditation isn't about stopping your thoughts.", "start_time": 0, "end_time": 3},
        {"sentence": "It's about observing them without judgment.", "start_time": 3, "end_time": 6},
        {"sentence": "When you practice mindfulness, you develop understanding.", "start_time": 6, "end_time": 10},
        {"sentence": "Lucid dreaming takes consciousness exploration to another level.", "start_time": 10, "end_time": 15},
    ]
    
    topics = extractor.extract_video_topics_enhanced(
        test_text,
        timestamps,
        title="Meditation and Consciousness",
        hashtags=["#meditation", "#mindfulness", "#luciddreaming"]
    )
    
    print("\n=== Extracted Topics ===")
    for topic in topics:
        print(f"\nTopic: {topic.tag}")
        print(f"  Canonical: {topic.canonical}")
        print(f"  Confidence: {topic.confidence}")
        print(f"  Sources: {', '.join(topic.sources)}")
        print(f"  Evidence: {len(topic.evidence)} sentences")
        if topic.evidence:
            print(f"  First occurrence: [{topic.evidence[0].start_time:.1f}s] {topic.evidence[0].text}")


if __name__ == "__main__":
    main()
