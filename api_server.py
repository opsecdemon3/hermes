#!/usr/bin/env python3
"""
FastAPI Server - Topic Intelligence API
Provides REST endpoints for accessing topics, transcripts, and analytics
"""

import json
import os  # Copilot addition: deployment prep
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import semantic search
from core.semantic_search.engine import SemanticSearchEngine


# Initialize FastAPI app
app = FastAPI(
    title="TikTalk Topic Intelligence API",
    description="REST API for TikTok transcript topics, analytics, and semantic search",
    version="3.0.0"
)

# Initialize semantic search engine
search_engine = SemanticSearchEngine()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class Tag(BaseModel):
    tag: str
    score: float
    type: str = "keyphrase"


class VideoTags(BaseModel):
    video_id: str
    title: str
    tags: List[Tag]
    extracted_at: str


class RankedTag(BaseModel):
    tag: str
    frequency: int
    avg_score: float
    engagement_weight: float
    combined_score: float
    video_ids: List[str]


class AccountTags(BaseModel):
    total_tags: int
    total_videos: int
    tags: List[RankedTag]


class AccountCategory(BaseModel):
    category: str
    confidence: float
    all_scores: Optional[Dict[str, float]] = None


# Semantic Search Models
class SearchFilters(BaseModel):
    """Filters for semantic search"""
    usernames: Optional[List[str]] = None  # Include only these creators
    exclude_usernames: Optional[List[str]] = None  # Exclude these creators
    tags: Optional[List[str]] = None  # Filter by topic tags
    category: Optional[str] = None  # Filter by creator category
    min_score: Optional[float] = 0.15  # Minimum relevance score (0.0-1.0)
    date_from: Optional[str] = None  # Start date (YYYY-MM-DD)
    date_to: Optional[str] = None  # End date (YYYY-MM-DD)
    exact_phrase: Optional[bool] = False  # Exact phrase matching


class SearchRequest(BaseModel):
    query: str
    top_k: int = 200  # High default to get all relevant results (filtered by score threshold)
    filters: Optional[SearchFilters] = None
    sort: str = "relevance"  # relevance, recency, timestamp


class SearchResult(BaseModel):
    text: str
    snippet: str
    video_id: str
    username: str
    timestamp: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    score: float
    segment_id: int


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]


# Helper functions
def get_account_dir(username: str, base_dir: str = "accounts") -> Path:
    """Get account directory path"""
    return Path(base_dir) / username.lstrip('@')


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load JSON file"""
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path.name}")
    
    with open(file_path, 'r') as f:
        return json.load(f)


# API Endpoints

@app.get("/")
async def root():
    """API root"""
    return {
        "name": "TikTalk Topic Intelligence API",
        "version": "3.0.0",
        "endpoints": {
            "accounts": "/api/accounts",
            "category": "/api/accounts/{username}/category",
            "tags": "/api/accounts/{username}/tags",
            "by_video": "/api/accounts/{username}/tags/by-video",
            "single_video": "/api/accounts/{username}/tags/video/{video_id}",
            "semantic_search": "/api/search/semantic",
            "search_stats": "/api/search/stats",
            "transcript": "/api/transcript/{username}/{video_id}"
        }
    }


@app.get("/api/accounts")
async def list_accounts(base_dir: str = "accounts"):
    """List all available accounts with extended metadata for frontend"""
    base_path = Path(base_dir)
    
    if not base_path.exists():
        return []
    
    accounts = []
    for account_dir in base_path.iterdir():
        if account_dir.is_dir() and not account_dir.name.startswith('_'):
            # Check if account has tags
            topics_dir = account_dir / "topics"
            has_tags = topics_dir.exists() and (topics_dir / "account_tags.json").exists()
            has_category = topics_dir.exists() and (topics_dir / "account_category.json").exists()
            
            # Check if account has transcripts
            index_file = account_dir / "index.json"
            has_transcripts = index_file.exists()
            
            # Get category if available
            category = None
            if has_category:
                try:
                    category_file = topics_dir / "account_category.json"
                    with open(category_file, 'r') as f:
                        category_data = json.load(f)
                        category = category_data.get('category')
                except:
                    pass
            
            # Get video count and last_updated from index
            video_count = 0
            last_updated = None
            top_topics = []
            
            if has_transcripts:
                try:
                    with open(index_file, 'r') as f:
                        index_data = json.load(f)
                        video_count = len([v for v in index_data.get('processed_videos', {}).values() if v.get('success')])
                        last_updated = index_data.get('last_updated')
                except:
                    pass
            
            # Get top topics if available
            if has_tags:
                try:
                    tags_file = topics_dir / "account_tags.json"
                    with open(tags_file, 'r') as f:
                        tags_data = json.load(f)
                        top_topics = [t['tag'] for t in tags_data.get('tags', [])[:5]]
                except:
                    pass
            
            accounts.append({
                "username": account_dir.name,
                "category": category,
                "video_count": video_count,
                "last_updated": last_updated,
                "top_topics": top_topics,
                "has_transcripts": has_transcripts,
                "has_tags": has_tags,
                "has_category": has_category
            })
    
    # Sort by video_count descending
    accounts.sort(key=lambda x: x['video_count'], reverse=True)
    
    return accounts


@app.get("/api/accounts/{username}/tags", response_model=AccountTags)
async def get_account_tags(
    username: str,
    top_n: Optional[int] = Query(None, description="Limit to top N tags"),
    min_frequency: Optional[int] = Query(None, description="Minimum tag frequency")
):
    """Get ranked tags for an account"""
    account_dir = get_account_dir(username)
    tags_file = account_dir / "topics" / "account_tags.json"
    
    data = load_json_file(tags_file)
    
    # Apply filters
    tags = data['tags']
    
    if min_frequency:
        tags = [t for t in tags if t['frequency'] >= min_frequency]
    
    if top_n:
        tags = tags[:top_n]
    
    return AccountTags(
        total_tags=len(tags),
        total_videos=data['total_videos'],
        tags=tags
    )


@app.get("/api/accounts/{username}/category", response_model=AccountCategory)
async def get_account_category(username: str):
    """Get broad category classification for an account"""
    account_dir = get_account_dir(username)
    category_file = account_dir / "topics" / "account_category.json"
    
    data = load_json_file(category_file)
    
    return AccountCategory(
        category=data['category'],
        confidence=data['confidence'],
        all_scores=data.get('all_scores')
    )


@app.get("/api/accounts/{username}/tags/by-video")
async def get_tags_by_video(username: str):
    """Get tags organized by video"""
    account_dir = get_account_dir(username)
    topics_dir = account_dir / "topics"
    
    if not topics_dir.exists():
        raise HTTPException(status_code=404, detail="Tags not found for this account")
    
    video_tags = []
    for tag_file in topics_dir.glob("*_tags.json"):
        if tag_file.name in ["account_tags.json", "account_category.json"]:
            continue
        
        data = load_json_file(tag_file)
        video_tags.append(data)
    
    # Sort by video_id
    video_tags.sort(key=lambda x: x['video_id'], reverse=True)
    
    return {
        "username": username,
        "total_videos": len(video_tags),
        "videos": video_tags
    }


@app.get("/api/accounts/{username}/tags/video/{video_id}", response_model=VideoTags)
async def get_video_tags(username: str, video_id: str):
    """Get tags for a specific video"""
    account_dir = get_account_dir(username)
    tag_file = account_dir / "topics" / f"{video_id}_tags.json"
    
    data = load_json_file(tag_file)
    return VideoTags(**data)


# ===== Topic System V2 Endpoints =====

@app.get("/api/video/{video_id}/topics")
async def get_video_topics_v2(
    video_id: str,
    spans: int = Query(0, description="Include timestamped evidence (1=yes, 0=no)"),
    min_conf: float = Query(0.0, description="Minimum confidence threshold (0.0-1.0)")
):
    """
    Get enhanced topics for a specific video (V2 format)
    
    Returns topics with canonical forms, confidence scores, and optional evidence spans.
    """
    # Find which account this video belongs to
    accounts_dir = Path("accounts")
    video_found = False
    username = None
    
    for account_dir in accounts_dir.iterdir():
        if not account_dir.is_dir():
            continue
        tag_file = account_dir / "topics" / f"{video_id}_tags.json"
        if tag_file.exists():
            video_found = True
            username = account_dir.name
            break
    
    if not video_found:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
    
    # Load video tags (V2 format if available, otherwise V1)
    tag_file = accounts_dir / username / "topics" / f"{video_id}_tags.json"
    data = load_json_file(tag_file)
    
    # Filter by confidence if specified
    tags = data.get('tags', [])
    if min_conf > 0:
        tags = [t for t in tags if t.get('confidence', 0.5) >= min_conf]
    
    # Filter evidence if not requested
    if spans == 0:
        for tag in tags:
            tag.pop('evidence', None)
    
    return {
        "video_id": video_id,
        "username": username,
        "title": data.get('title', ''),
        "total_topics": len(tags),
        "topics": tags
    }


@app.get("/api/accounts/{username}/topics")
async def get_account_topics_v2(
    username: str,
    canonical: int = Query(0, description="Group by canonical form (1=yes, 0=no)"),
    min_conf: float = Query(0.0, description="Minimum confidence threshold"),
    source: Optional[str] = Query(None, description="Filter by source: transcript, hashtag, or all")
):
    """
    Get enhanced topics for an account (V2 format)
    
    Returns topics with canonical grouping, confidence filtering, and source filtering.
    """
    account_dir = get_account_dir(username)
    tags_file = account_dir / "topics" / "account_tags.json"
    
    data = load_json_file(tags_file)
    tags = data.get('tags', [])
    
    # Filter by confidence
    if min_conf > 0:
        tags = [t for t in tags if t.get('confidence', t.get('avg_score', 0.5)) >= min_conf]
    
    # Filter by source
    if source and source != 'all':
        tags = [t for t in tags if t.get('source', 'transcript') == source]
    
    # Group by canonical if requested
    if canonical == 1:
        canonical_groups = {}
        for tag in tags:
            canon = tag.get('canonical', tag['tag'])
            if canon not in canonical_groups:
                canonical_groups[canon] = {
                    'canonical': canon,
                    'variants': [],
                    'total_frequency': 0,
                    'avg_confidence': 0.0,
                    'video_ids': set()
                }
            
            canonical_groups[canon]['variants'].append(tag['tag'])
            canonical_groups[canon]['total_frequency'] += tag.get('frequency', 1)
            canonical_groups[canon]['avg_confidence'] += tag.get('confidence', tag.get('avg_score', 0.5))
            canonical_groups[canon]['video_ids'].update(tag.get('video_ids', []))
        
        # Average confidence and convert sets
        for canon, group in canonical_groups.items():
            group['avg_confidence'] /= len(group['variants'])
            group['video_ids'] = sorted(list(group['video_ids']))
        
        # Sort by frequency
        canonical_list = sorted(
            canonical_groups.values(),
            key=lambda x: x['total_frequency'],
            reverse=True
        )
        
        return {
            "username": username,
            "total_canonical": len(canonical_list),
            "total_variants": len(tags),
            "groups": canonical_list
        }
    
    return {
        "username": username,
        "total_topics": len(tags),
        "topics": tags
    }


@app.get("/api/accounts/{username}/umbrellas")
async def get_account_umbrellas(username: str):
    """
    Get topic umbrellas (semantic clusters) for an account
    
    Returns high-level topic groupings with member topics, coherence scores, and stats.
    """
    account_dir = get_account_dir(username)
    umbrellas_file = account_dir / "topics" / "topic_umbrellas.json"
    
    if not umbrellas_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Umbrellas not generated for @{username}. Run: python umbrella_builder.py build --account {username}"
        )
    
    data = load_json_file(umbrellas_file)
    
    return {
        "username": data.get('username'),
        "total_topics": data.get('total_topics'),
        "canonical_topics": data.get('canonical_topics'),
        "umbrella_count": data.get('umbrella_count'),
        "clustering_method": data.get('clustering_method'),
        "umbrellas": data.get('umbrellas', [])
    }


@app.post("/api/topics/reindex")
async def reindex_topics(
    username: Optional[str] = None,
    reindex_all: bool = False
):
    """
    Trigger re-indexing of topics using Topic System V2
    
    This is an async operation that returns a job_id for tracking progress.
    """
    import uuid
    import asyncio
    from datetime import datetime
    
    job_id = str(uuid.uuid4())
    
    # TODO: Implement actual reindexing with job tracking
    # For now, return a placeholder
    
    if reindex_all:
        accounts_to_process = []
        accounts_dir = Path("accounts")
        for account_dir in accounts_dir.iterdir():
            if account_dir.is_dir():
                index_file = account_dir / "index.json"
                if index_file.exists():
                    accounts_to_process.append(account_dir.name)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "accounts": accounts_to_process,
            "total_accounts": len(accounts_to_process),
            "message": f"Reindexing queued for {len(accounts_to_process)} accounts",
            "created_at": datetime.now().isoformat()
        }
    
    elif username:
        account_dir = get_account_dir(username)
        if not account_dir.exists():
            raise HTTPException(status_code=404, detail=f"Account @{username} not found")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "accounts": [username],
            "total_accounts": 1,
            "message": f"Reindexing queued for @{username}",
            "created_at": datetime.now().isoformat()
        }
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Must specify either 'username' or 'reindex_all=true'"
        )


@app.get("/api/transcripts")
async def get_all_transcripts(
    username: Optional[str] = Query(None, description="Filter by username"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by topic tag"),
    sort: str = Query("recent", description="Sort by: recent, oldest, creator, duration"),
    limit: Optional[int] = Query(None, description="Limit results"),
    offset: int = Query(0, description="Offset for pagination"),
    base_dir: str = "accounts"
):
    """Get all transcripts across all accounts with filtering and sorting"""
    base_path = Path(base_dir)
    
    if not base_path.exists():
        return {
            "total": 0,
            "transcripts": []
        }
    
    all_transcripts = []
    
    # Iterate through all accounts
    for account_dir in base_path.iterdir():
        if not account_dir.is_dir() or account_dir.name.startswith('_'):
            continue
            
        account_username = account_dir.name
        
        # Apply username filter
        if username and account_username != username.lstrip('@'):
            continue
        
        index_file = account_dir / "index.json"
        if not index_file.exists():
            continue
        
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
        except:
            continue
        
        # Get account category
        account_category = None
        category_file = account_dir / "topics" / "account_category.json"
        if category_file.exists():
            try:
                with open(category_file, 'r') as f:
                    cat_data = json.load(f)
                    account_category = cat_data.get('category')
            except:
                pass
        
        # Apply category filter
        if category and account_category != category:
            continue
        
        # Get account tags for filtering
        account_tags = []
        tags_file = account_dir / "topics" / "account_tags.json"
        if tags_file.exists():
            try:
                with open(tags_file, 'r') as f:
                    tags_data = json.load(f)
                    account_tags = [t['tag'] for t in tags_data.get('tags', [])]
            except:
                pass
        
        # Apply tag filter
        if tag and tag.lower() not in [t.lower() for t in account_tags]:
            continue
        
        # Process each video
        for video_id, video_data in index_data.get('processed_videos', {}).items():
            if not video_data.get('success'):
                continue
            
            # Get video-specific tags
            video_tags = []
            video_tag_file = account_dir / "topics" / f"{video_id}_tags.json"
            if video_tag_file.exists():
                try:
                    with open(video_tag_file, 'r') as f:
                        video_tag_data = json.load(f)
                        video_tags = [t['tag'] for t in video_tag_data.get('tags', [])][:5]
                except:
                    pass
            
            # Count segments for metadata using TimestampExtractor
            segment_count = 0
            transcript_file = account_dir / "transcriptions" / f"{video_id}_transcript.txt"
            if transcript_file.exists():
                try:
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract transcript text (skip header)
                    if "=" * 50 in content:
                        transcript_text = content.split("=" * 50, 1)[1].strip()
                    else:
                        transcript_text = content
                    
                    # Count sentences using TimestampExtractor
                    from core.semantic_search.timestamp_extractor import TimestampExtractor
                    timestamp_extractor = TimestampExtractor()
                    sentences = timestamp_extractor.extract_sentence_timestamps(transcript_text)
                    segment_count = len(sentences)
                except Exception as e:
                    # Fallback: estimate based on length (roughly 1 sentence per 100 chars)
                    segment_count = video_data.get('transcription_length', 0) // 100
            
            all_transcripts.append({
                "username": account_username,
                "video_id": video_id,
                "title": video_data.get('title', ''),
                "duration": video_data.get('duration', 0),
                "processed_at": video_data.get('processed_at'),
                "url": video_data.get('url', ''),
                "category": account_category,
                "tags": video_tags,
                "segment_count": segment_count,
                "transcription_length": video_data.get('transcription_length', 0)
            })
    
    # Sort transcripts
    if sort == "recent":
        all_transcripts.sort(key=lambda x: x.get('processed_at', ''), reverse=True)
    elif sort == "oldest":
        all_transcripts.sort(key=lambda x: x.get('processed_at', ''))
    elif sort == "creator":
        all_transcripts.sort(key=lambda x: x['username'])
    elif sort == "duration":
        all_transcripts.sort(key=lambda x: x['duration'], reverse=True)
    
    # Apply pagination
    total = len(all_transcripts)
    if limit:
        all_transcripts = all_transcripts[offset:offset + limit]
    elif offset:
        all_transcripts = all_transcripts[offset:]
    
    return {
        "total": total,
        "count": len(all_transcripts),
        "offset": offset,
        "transcripts": all_transcripts
    }


@app.get("/api/accounts/{username}/transcripts")
async def get_account_transcripts(username: str):
    """Get all transcripts for an account"""
    account_dir = get_account_dir(username)
    index_file = account_dir / "index.json"
    
    index_data = load_json_file(index_file)
    
    transcripts = []
    for video_id, video_data in index_data.get('processed_videos', {}).items():
        if video_data.get('success'):
            transcript_file = account_dir / "transcriptions" / f"{video_id}_transcript.txt"
            
            if transcript_file.exists():
                with open(transcript_file, 'r') as f:
                    content = f.read()
                
                # Extract transcription text
                if "=" * 50 in content:
                    transcript_text = content.split("=" * 50, 1)[1].strip()
                else:
                    transcript_text = content
                
                transcripts.append({
                    "video_id": video_id,
                    "title": video_data.get('title', ''),
                    "transcript": transcript_text,
                    "length": len(transcript_text)
                })
    
    return {
        "username": username,
        "total_transcripts": len(transcripts),
        "transcripts": transcripts
    }


@app.get("/api/accounts/{username}/stats")
async def get_account_stats(username: str):
    """Get overall stats for an account"""
    account_dir = get_account_dir(username)
    index_file = account_dir / "index.json"
    
    index_data = load_json_file(index_file)
    
    # Check for tags and category
    tags_file = account_dir / "topics" / "account_tags.json"
    category_file = account_dir / "topics" / "account_category.json"
    has_tags = tags_file.exists()
    has_category = category_file.exists()
    
    total_tags = 0
    category = None
    
    if has_tags:
        tags_data = load_json_file(tags_file)
        total_tags = tags_data['total_tags']
    
    if has_category:
        category_data = load_json_file(category_file)
        category = category_data['category']
    
    return {
        "username": username,
        "account": index_data.get('account'),
        "stats": index_data.get('stats', {}),
        "has_tags": has_tags,
        "has_category": has_category,
        "category": category,
        "total_unique_tags": total_tags,
        "created_at": index_data.get('created_at'),
        "last_updated": index_data.get('last_updated')
    }


@app.post("/api/search/semantic")
async def semantic_search(request: SearchRequest):
    """Perform semantic search with comprehensive filtering - returns ranked results"""
    try:
        from datetime import datetime
        
        # Get initial search results
        top_k = request.top_k if request.top_k and request.top_k > 0 else 200
        results = search_engine.search(request.query, top_k)
        
        # Apply filters
        filters = request.filters
        min_score = filters.min_score if filters and filters.min_score else 0.15
        
        # Filter by minimum relevance score
        filtered_results = [r for r in results if r.get('score', 0) > min_score]
        
        # Filter by username (include)
        if filters and filters.usernames and len(filters.usernames) > 0:
            filtered_results = [r for r in filtered_results if r.get('username') in filters.usernames]
        
        # Filter by username (exclude)
        if filters and filters.exclude_usernames and len(filters.exclude_usernames) > 0:
            filtered_results = [r for r in filtered_results if r.get('username') not in filters.exclude_usernames]
        
        # Filter by category
        if filters and filters.category:
            # Load creator categories
            creator_categories = {}
            base_path = Path("accounts")
            if base_path.exists():
                for creator_dir in base_path.iterdir():
                    if creator_dir.is_dir() and not creator_dir.name.startswith('_'):
                        category_file = creator_dir / "topics" / "account_category.json"
                        if category_file.exists():
                            with open(category_file, 'r') as f:
                                cat_data = json.load(f)
                                creator_categories[creator_dir.name] = cat_data.get('category')
            
            # Filter by category
            filtered_results = [r for r in filtered_results 
                              if creator_categories.get(r.get('username')) == filters.category]
        
        # Filter by tags (if video has matching tags)
        if filters and filters.tags and len(filters.tags) > 0:
            # Load video tags
            video_tags = {}
            base_path = Path("accounts")
            if base_path.exists():
                for creator_dir in base_path.iterdir():
                    if creator_dir.is_dir() and not creator_dir.name.startswith('_'):
                        topics_dir = creator_dir / "topics"
                        if topics_dir.exists():
                            for tag_file in topics_dir.glob("*_tags.json"):
                                video_id = tag_file.stem.replace('_tags', '')
                                with open(tag_file, 'r') as f:
                                    tag_data = json.load(f)
                                    video_tags[f"{creator_dir.name}/{video_id}"] = [
                                        t.get('tag', '').lower() for t in tag_data.get('tags', [])
                                    ]
            
            # Filter results by tag match
            filter_tags_lower = [t.lower() for t in filters.tags]
            filtered_results = [r for r in filtered_results
                              if any(tag in video_tags.get(f"{r.get('username')}/{r.get('video_id')}", [])
                                   for tag in filter_tags_lower)]
        
        # Filter by date range (if available in index metadata)
        if filters and (filters.date_from or filters.date_to):
            # Load video metadata from index.json files
            video_dates = {}
            base_path = Path("accounts")
            if base_path.exists():
                for creator_dir in base_path.iterdir():
                    if creator_dir.is_dir() and not creator_dir.name.startswith('_'):
                        index_file = creator_dir / "index.json"
                        if index_file.exists():
                            with open(index_file, 'r') as f:
                                index_data = json.load(f)
                                for video_id, video_info in index_data.get('processed_videos', {}).items():
                                    processed_at = video_info.get('processed_at', '')
                                    if processed_at:
                                        video_dates[f"{creator_dir.name}/{video_id}"] = processed_at
            
            # Filter by date
            if filters.date_from:
                date_from = datetime.fromisoformat(filters.date_from.replace('Z', '+00:00'))
                filtered_results = [r for r in filtered_results
                                  if (video_dates.get(f"{r.get('username')}/{r.get('video_id')}")
                                      and datetime.fromisoformat(video_dates[f"{r.get('username')}/{r.get('video_id')}"].replace('Z', '+00:00')) >= date_from)]
            
            if filters.date_to:
                date_to = datetime.fromisoformat(filters.date_to.replace('Z', '+00:00'))
                filtered_results = [r for r in filtered_results
                                  if (video_dates.get(f"{r.get('username')}/{r.get('video_id')}")
                                      and datetime.fromisoformat(video_dates[f"{r.get('username')}/{r.get('video_id')}"].replace('Z', '+00:00')) <= date_to)]
        
        # Sort results
        sort_by = request.sort if request.sort else "relevance"
        if sort_by == "recency":
            # Sort by date (newest first) - requires date metadata
            video_dates = {}
            base_path = Path("accounts")
            if base_path.exists():
                for creator_dir in base_path.iterdir():
                    if creator_dir.is_dir() and not creator_dir.name.startswith('_'):
                        index_file = creator_dir / "index.json"
                        if index_file.exists():
                            with open(index_file, 'r') as f:
                                index_data = json.load(f)
                                for video_id, video_info in index_data.get('processed_videos', {}).items():
                                    video_dates[f"{creator_dir.name}/{video_id}"] = video_info.get('processed_at', '')
            
            filtered_results.sort(key=lambda r: video_dates.get(f"{r.get('username')}/{r.get('video_id')}", ''), reverse=True)
        
        elif sort_by == "timestamp":
            # Sort by timestamp position in video (start -> end)
            filtered_results.sort(key=lambda r: r.get('start_time', 0))
        
        # else: sort_by == "relevance" is already sorted by score from search_engine
        
        return filtered_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/api/search/stats")
async def get_search_stats():
    """Get semantic search index statistics"""
    try:
        stats = search_engine.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")


@app.get("/api/search/filter-options")
async def get_filter_options():
    """Get available filter options for search"""
    try:
        base_path = Path("accounts")
        
        # Get all creators
        creators = []
        categories = set()
        all_tags = set()
        
        if base_path.exists():
            for creator_dir in base_path.iterdir():
                if creator_dir.is_dir() and not creator_dir.name.startswith('_'):
                    username = creator_dir.name
                    creators.append(username)
                    
                    # Get category
                    category_file = creator_dir / "topics" / "account_category.json"
                    if category_file.exists():
                        with open(category_file, 'r') as f:
                            cat_data = json.load(f)
                            category = cat_data.get('category')
                            if category:
                                categories.add(category)
                    
                    # Get all tags from this creator
                    topics_dir = creator_dir / "topics"
                    if topics_dir.exists():
                        for tag_file in topics_dir.glob("*_tags.json"):
                            with open(tag_file, 'r') as f:
                                tag_data = json.load(f)
                                for tag_info in tag_data.get('tags', []):
                                    tag = tag_info.get('tag', '').strip()
                                    if tag:
                                        all_tags.add(tag)
        
        return {
            "creators": sorted(creators),
            "categories": sorted(list(categories)),
            "tags": sorted(list(all_tags))[:100],  # Limit to top 100 most common
            "score_range": {"min": 0.0, "max": 1.0, "default": 0.15}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter options error: {str(e)}")


@app.get("/api/transcript/{username}/{video_id}")
async def get_transcript(username: str, video_id: str, query: Optional[str] = None, highlights: Optional[str] = None):
    """Get full transcript with optional multi-highlight support
    
    Args:
        username: Creator username
        video_id: Video ID
        query: Optional search query to find and highlight all matching segments
        highlights: Optional comma-separated timestamps to highlight (e.g., "00:10,01:30,02:45")
    """
    try:
        # Load transcript file
        transcript_path = Path("accounts") / username / "transcriptions" / f"{video_id}_transcript.txt"
        
        if not transcript_path.exists():
            raise HTTPException(status_code=404, detail=f"Transcript not found for {username}/{video_id}")
        
        # Read transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_content = f.read()
        
        # Extract transcript text
        if "=" * 50 in transcript_content:
            transcript_text = transcript_content.split("=" * 50, 1)[1].strip()
        else:
            transcript_text = transcript_content
        
        # Extract timestamps
        from core.semantic_search.timestamp_extractor import TimestampExtractor
        timestamp_extractor = TimestampExtractor()
        sentences = timestamp_extractor.extract_sentence_timestamps(transcript_text)
        
        # Helper function to format timestamp
        def format_timestamp(seconds: float) -> str:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"
        
        # Determine which segments to highlight
        highlight_indices = set()
        
        if query:
            # If query provided, find ALL matching segments using semantic search
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            query_embedding = model.encode([query], convert_to_numpy=True)[0]
            
            # Calculate similarity for each sentence
            for idx, sentence in enumerate(sentences):
                sentence_text = sentence["sentence"]
                sentence_embedding = model.encode([sentence_text], convert_to_numpy=True)[0]
                
                # Cosine similarity
                import numpy as np
                similarity = np.dot(query_embedding, sentence_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(sentence_embedding)
                )
                
                # Highlight if similarity is above threshold (0.3 is moderate match)
                if similarity > 0.3:
                    highlight_indices.add(idx)
        
        elif highlights:
            # If specific timestamps provided, highlight those
            highlight_times = []
            for ts in highlights.split(','):
                ts = ts.strip()
                if ':' in ts:
                    parts = ts.split(':')
                    if len(parts) == 2:
                        minutes, seconds = map(int, parts)
                        highlight_times.append(minutes * 60 + seconds)
            
            # Find sentences matching these timestamps (within 5 second tolerance)
            for idx, sentence in enumerate(sentences):
                start_time = sentence.get("start_time", 0)
                for target_time in highlight_times:
                    if abs(start_time - target_time) < 5:
                        highlight_indices.add(idx)
                        break
        
        # Build FULL transcript with highlights
        segments = []
        for idx, sentence in enumerate(sentences):
            segments.append({
                "timestamp": format_timestamp(sentence.get("start_time", 0)),
                "text": sentence["sentence"],
                "highlighted": idx in highlight_indices,
                "start_time": sentence.get("start_time", 0),
                "end_time": sentence.get("end_time", 0)
            })
        
        return {
            "username": username,
            "video_id": video_id,
            "segments": segments,
            "total_segments": len(segments),
            "highlighted_count": len(highlight_indices)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcript error: {str(e)}")


def _calculate_system_status():
    """Helper function to calculate system status"""
    # Get total creators
    base_path = Path("accounts")
    total_creators = 0
    total_transcripts = 0
    
    if base_path.exists():
        creators = [d for d in base_path.iterdir() if d.is_dir() and not d.name.startswith('_')]
        total_creators = len(creators)
        
        # Count total successful transcripts
        for creator_dir in creators:
            index_file = creator_dir / "index.json"
            if index_file.exists():
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
                    total_transcripts += len([v for v in index_data.get('processed_videos', {}).values() if v.get('success')])
    
    # Get search index stats
    stats = search_engine.get_stats()
    total_vectors = stats.get('total_vectors', 0)
    
    # Determine status
    status = "healthy" if total_creators > 0 and total_vectors > 0 else "warning"
    
    return {
        "total_creators": total_creators,
        "total_transcripts": total_transcripts,
        "total_vectors": total_vectors,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/verify/system")
async def verify_system():
    """Get system status for dashboard"""
    try:
        return _calculate_system_status()
    except Exception as e:
        return {
            "total_creators": 0,
            "total_transcripts": 0,
            "total_vectors": 0,
            "status": "error",
            "error": str(e)
        }


@app.post("/api/verify/system")
async def reverify_system():
    """Re-verify system status (force refresh)"""
    try:
        # Force re-calculation (could add cache invalidation here if needed)
        return _calculate_system_status()
    except Exception as e:
        return {
            "total_creators": 0,
            "total_transcripts": 0,
            "total_vectors": 0,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# INGESTION QUEUE ENDPOINTS
# ============================================================================

# Import ingestion manager
from core.ingestion_manager import queue_manager, VideoFilter, IngestionSettings
import asyncio

# Background task tracker
background_tasks = {}


class IngestionRequest(BaseModel):
    """Request to start ingestion"""
    usernames: List[str]  # List of usernames to ingest
    filters: Optional[Dict[str, Any]] = None  # Video filters
    settings: Optional[Dict[str, Any]] = None  # Ingestion settings


@app.post("/api/ingest/start")
async def start_ingestion(request: IngestionRequest):
    """
    Start a new ingestion job with filtering
    
    Request body:
    {
        "usernames": ["creator1", "creator2"],
        "filters": {
            "last_n_videos": 10,
            "only_with_speech": true,
            "required_category": "Health"
        },
        "settings": {
            "whisper_mode": "balanced",
            "skip_existing": true
        }
    }
    """
    try:
        # Map UI-friendly names to actual Whisper model names
        whisper_model_map = {
            "fast": "tiny",
            "balanced": "small",
            "accurate": "medium",
            "ultra": "large-v3"
        }
        
        # Convert settings if whisper_mode is present
        settings = request.settings or {}
        if "whisper_mode" in settings:
            ui_mode = settings["whisper_mode"]
            settings["whisper_mode"] = whisper_model_map.get(ui_mode, ui_mode)
        
        # Create job
        job_id = queue_manager.create_job(
            usernames=request.usernames,
            filters=request.filters,
            settings=settings
        )
        
        # Start background task
        task = asyncio.create_task(queue_manager.run_ingestion(job_id))
        background_tasks[job_id] = task
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Ingestion job created for {len(request.usernames)} account(s)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start ingestion: {str(e)}")


@app.get("/api/ingest/status/{job_id}")
async def get_ingestion_status(job_id: str):
    """Get status of an ingestion job"""
    status = queue_manager.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@app.get("/api/ingest/jobs")
async def list_ingestion_jobs():
    """List all ingestion jobs"""
    return {
        "jobs": queue_manager.list_jobs()
    }


@app.post("/api/ingest/pause/{job_id}")
async def pause_ingestion(job_id: str):
    """Pause an ingestion job"""
    success = await queue_manager.pause_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause job (not found or already complete)")
    return {"status": "paused"}


@app.post("/api/ingest/resume/{job_id}")
async def resume_ingestion(job_id: str):
    """Resume a paused ingestion job"""
    success = await queue_manager.resume_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume job (not found or not paused)")
    
    # Restart background task if not running
    job = queue_manager.get_job(job_id)
    if job and job_id not in background_tasks:
        task = asyncio.create_task(queue_manager.run_ingestion(job_id))
        background_tasks[job_id] = task
    
    return {"status": "resumed"}


@app.post("/api/ingest/cancel/{job_id}")
async def cancel_ingestion(job_id: str):
    """Cancel an ingestion job"""
    success = await queue_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel job (not found or already complete)")
    return {"status": "cancelled"}


@app.get("/api/ingest/metadata/{username}")
async def get_account_metadata(username: str):
    """
    Fetch video metadata for an account (for filtering preview)
    Does NOT start ingestion, just fetches metadata
    """
    try:
        videos = await queue_manager.fetch_video_metadata(username.lstrip('@'))
        
        # Return simplified metadata for UI
        return {
            "username": username,
            "total_videos": len(videos),
            "videos": [
                {
                    "video_id": v.get('video_id'),
                    "title": v.get('title', ''),
                    "view_count": v.get('view_count', 0),
                    "create_time": v.get('create_time', 0),
                    "duration": v.get('duration', 0)
                }
                for v in videos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metadata: {str(e)}")


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server"""
    print(f"\n{'='*80}")
    print(f"🚀 Starting TikTalk Topic Intelligence API")
    print(f"{'='*80}\n")
    print(f"Server running at: http://{host}:{port}")
    print(f"API docs: http://{host}:{port}/docs")
    print(f"OpenAPI spec: http://{host}:{port}/openapi.json")
    print(f"\n{'='*80}\n")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse
    
    # Copilot addition: deployment prep - read from environment first
    parser = argparse.ArgumentParser(description='Start TikTalk API server')
    parser.add_argument('--host', default=os.getenv('API_HOST', '0.0.0.0'), help='Host to bind to')
    parser.add_argument('--port', type=int, default=int(os.getenv('API_PORT', '8000')), help='Port to bind to')
    
    args = parser.parse_args()
    start_server(args.host, args.port)

