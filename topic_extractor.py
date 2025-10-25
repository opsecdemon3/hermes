#!/usr/bin/env python3
"""
Topic Extraction Engine - Semantic topic extraction using embeddings
Uses KeyBERT and sentence-transformers for real semantic understanding
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from collections import Counter, defaultdict
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

# NLP imports
try:
    from keybert import KeyBERT
    from sentence_transformers import SentenceTransformer
    import nltk
    from nltk.corpus import stopwords
    HAS_NLP = True
except ImportError:
    HAS_NLP = False
    print("⚠️  NLP libraries not installed. Install with: pip install -r requirements.txt")


# Predefined broad categories for account classification
BROAD_CATEGORIES = [
    "Philosophy",
    "Spirituality", 
    "Self-Improvement",
    "Psychology",
    "Business",
    "Health",
    "Tech",
    "Politics",
    "History",
    "Creativity",
    "Education",
    "Entertainment",
    "Music",
    "Art",
    "Science"
]


class TopicExtractor:
    """Extract semantic tags from transcripts using embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize topic extractor
        
        Args:
            model_name: Sentence transformer model to use
        """
        if not HAS_NLP:
            raise ImportError("NLP libraries required. Run: pip install keybert sentence-transformers nltk scikit-learn")
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.logger.info(f"Loading sentence transformer: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.kw_model = KeyBERT(model=self.model)
        
        # Pre-compute category embeddings
        self.category_embeddings = self.model.encode(BROAD_CATEGORIES)
        self.logger.debug(f"Pre-computed embeddings for {len(BROAD_CATEGORIES)} categories")
        
        # Download NLTK stopwords if needed
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            try:
                self.logger.info("Downloading NLTK stopwords...")
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
                nltk.download('stopwords', quiet=True)
                self.stop_words = set(stopwords.words('english'))
            except Exception:
                # Fallback to built-in minimal stopwords list
                self.logger.warning("Using fallback stopwords list")
                self.stop_words = {
                    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
                    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
                    'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them',
                    'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll",
                    'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
                    'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or',
                    'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
                    'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
                    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once'
                }
        
        self.logger.info("Topic extractor initialized")
    
    def extract_video_tags(self, 
                          transcript: str,
                          min_tags: int = 3,
                          max_tags: int = 10,
                          diversity: float = 0.5) -> List[Dict[str, Any]]:
        """
        Extract semantic tags from a single video transcript
        
        Args:
            transcript: Video transcript text
            min_tags: Minimum number of tags to extract
            max_tags: Maximum number of tags to extract
            diversity: Diversity of tags (0-1, higher = more diverse)
            
        Returns:
            List of tags with scores
        """
        if not transcript or len(transcript) < 50:
            self.logger.warning("Transcript too short for tag extraction")
            return []
        
        try:
            # Extract keywords using MaxSum for diversity
            keywords = self.kw_model.extract_keywords(
                transcript,
                keyphrase_ngram_range=(1, 3),  # 1-3 word phrases
                stop_words='english',
                use_maxsum=True,
                nr_candidates=20,
                top_n=max_tags,
                diversity=diversity
            )
            
            # Convert to tag format
            tags = []
            for keyword, score in keywords:
                # Skip if too short or just stopwords
                if len(keyword.split()) == 1 and keyword.lower() in self.stop_words:
                    continue
                
                tags.append({
                    "tag": keyword,
                    "score": float(score),
                    "type": "keyphrase"
                })
            
            # Ensure minimum tags
            if len(tags) < min_tags:
                self.logger.warning(f"Only extracted {len(tags)} tags (min: {min_tags})")
            
            return tags[:max_tags]
            
        except Exception as e:
            self.logger.error(f"Error extracting tags: {e}")
            return []
    
    def aggregate_account_tags(self, 
                              video_tags: List[Dict[str, Any]],
                              video_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate tags from all videos in an account
        
        Args:
            video_tags: List of tag dictionaries from all videos
            video_metadata: List of video metadata (for engagement weights)
            
        Returns:
            Aggregated tags with rankings
        """
        tag_counts = Counter()
        tag_scores = defaultdict(list)
        tag_videos = defaultdict(list)
        
        # Create video_id -> metadata mapping
        video_meta_map = {v['video_id']: v for v in video_metadata}
        
        # Aggregate tags
        for video_tag_data in video_tags:
            video_id = video_tag_data.get('video_id')
            for tag_item in video_tag_data.get('tags', []):
                tag = tag_item['tag']
                score = tag_item['score']
                
                tag_counts[tag] += 1
                tag_scores[tag].append(score)
                tag_videos[tag].append(video_id)
        
        # Calculate weighted scores
        ranked_tags = []
        for tag, count in tag_counts.items():
            avg_score = np.mean(tag_scores[tag])
            
            # Calculate engagement weight (if metadata available)
            engagement_weight = 1.0
            total_views = 0
            for video_id in tag_videos[tag]:
                if video_id in video_meta_map:
                    total_views += video_meta_map[video_id].get('view_count', 0)
            
            if total_views > 0:
                engagement_weight = 1 + (np.log1p(total_views) / 20)  # Logarithmic scaling
            
            # Combined score: frequency × avg_score × engagement
            combined_score = count * avg_score * engagement_weight
            
            ranked_tags.append({
                "tag": tag,
                "frequency": count,
                "avg_score": float(avg_score),
                "engagement_weight": float(engagement_weight),
                "combined_score": float(combined_score),
                "video_ids": tag_videos[tag]
            })
        
        # Sort by combined score
        ranked_tags.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return {
            "total_tags": len(ranked_tags),
            "total_videos": len(video_tags),
            "tags": ranked_tags
        }
    
    def classify_account_category(self, top_tags: List[str], top_n: int = 10) -> Dict[str, Any]:
        """
        Classify account into a broad category using embedding similarity
        
        Args:
            top_tags: List of top tags from account
            top_n: Number of top tags to consider
            
        Returns:
            Category classification with confidence
        """
        if not top_tags:
            return {"category": "Unknown", "confidence": 0.0}
        
        try:
            # Use top N tags
            tags_to_use = top_tags[:top_n]
            
            # Generate embeddings for top tags
            tag_embeddings = self.model.encode(tags_to_use)
            
            # Compute average embedding (represents account's semantic space)
            account_embedding = np.mean(tag_embeddings, axis=0)
            
            # Compute cosine similarity with each category
            similarities = cosine_similarity(
                account_embedding.reshape(1, -1),
                self.category_embeddings
            )[0]
            
            # Find best match
            best_idx = np.argmax(similarities)
            best_category = BROAD_CATEGORIES[best_idx]
            confidence = float(similarities[best_idx])
            
            self.logger.info(f"Classified as '{best_category}' with confidence {confidence:.2f}")
            
            return {
                "category": best_category,
                "confidence": confidence,
                "all_scores": {
                    cat: float(sim) 
                    for cat, sim in zip(BROAD_CATEGORIES, similarities)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error classifying account category: {e}")
            return {"category": "Unknown", "confidence": 0.0}


class AccountTopicManager:
    """Manage tags and category for a TikTok account"""
    
    def __init__(self, username: str, base_dir: str = "accounts"):
        """
        Initialize account topic manager
        
        Args:
            username: TikTok username
            base_dir: Base directory for accounts
        """
        self.username = username.lstrip('@')
        self.base_dir = Path(base_dir)
        self.account_dir = self.base_dir / self.username
        self.transcriptions_dir = self.account_dir / "transcriptions"
        self.topics_dir = self.account_dir / "topics"
        self.index_file = self.account_dir / "index.json"
        
        # Create topics directory
        self.topics_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize tag extractor
        self.extractor = TopicExtractor()
    
    def extract_all_topics(self, force: bool = False) -> Dict[str, Any]:
        """
        Extract tags for all videos in account
        
        Args:
            force: Force re-extraction even if tags exist
            
        Returns:
            Extraction results
        """
        # Load index
        if not self.index_file.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_file}")
        
        with open(self.index_file, 'r') as f:
            index = json.load(f)
        
        processed_videos = index.get('processed_videos', {})
        
        results = {
            "username": self.username,
            "total_videos": len(processed_videos),
            "extracted": 0,
            "skipped": 0,
            "failed": 0,
            "video_tags": []
        }
        
        self.logger.info(f"Extracting tags for {len(processed_videos)} videos...")
        
        for video_id, video_data in processed_videos.items():
            if not video_data.get('success'):
                results['skipped'] += 1
                continue
            
            # Check if tags already exist
            tag_file = self.topics_dir / f"{video_id}_tags.json"
            if tag_file.exists() and not force:
                self.logger.debug(f"Tags already exist for {video_id}, skipping")
                results['skipped'] += 1
                
                # Load existing tags
                with open(tag_file, 'r') as f:
                    existing_tags = json.load(f)
                    results['video_tags'].append(existing_tags)
                continue
            
            # Load transcript
            transcript_file = self.transcriptions_dir / f"{video_id}_transcript.txt"
            if not transcript_file.exists():
                self.logger.warning(f"Transcript not found for {video_id}")
                results['failed'] += 1
                continue
            
            with open(transcript_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract transcription (after header)
            if "=" * 50 in content:
                transcript = content.split("=" * 50, 1)[1].strip()
            else:
                transcript = content
            
            # Extract tags
            try:
                tags = self.extractor.extract_video_tags(transcript)
                
                video_tags = {
                    "video_id": video_id,
                    "title": video_data.get('title', ''),
                    "tags": tags,
                    "extracted_at": pd.Timestamp.now().isoformat()
                }
                
                # Save tags
                with open(tag_file, 'w') as f:
                    json.dump(video_tags, f, indent=2)
                
                results['extracted'] += 1
                results['video_tags'].append(video_tags)
                
                self.logger.info(f"Extracted {len(tags)} tags for video {video_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to extract tags for {video_id}: {e}")
                results['failed'] += 1
        
        # Generate account-level aggregations
        if results['video_tags']:
            self._generate_account_aggregations(results['video_tags'], list(processed_videos.values()))
        
        return results
    
    def _generate_account_aggregations(self, video_tags: List[Dict], video_metadata: List[Dict]):
        """Generate account-level tag aggregations and category classification"""
        # Aggregate tags
        account_tags = self.extractor.aggregate_account_tags(video_tags, video_metadata)
        
        # Save account tags
        account_tags_file = self.topics_dir / "account_tags.json"
        with open(account_tags_file, 'w') as f:
            json.dump(account_tags, f, indent=2)
        
        self.logger.info(f"Saved account tags: {account_tags['total_tags']} unique tags")
        
        # Classify account category
        all_tags = [t['tag'] for t in account_tags['tags']]
        category = self.extractor.classify_account_category(all_tags, top_n=10)
        
        # Save account category
        category_file = self.topics_dir / "account_category.json"
        with open(category_file, 'w') as f:
            json.dump(category, f, indent=2)
        
        self.logger.info(f"Classified as '{category['category']}' (confidence: {category['confidence']:.2f})")


# Import pandas for timestamp
import pandas as pd

