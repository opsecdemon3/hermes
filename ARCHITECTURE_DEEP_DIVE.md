# TikTalk Architecture Deep Dive

**Repository**: TikTalk  
**Owner**: opsecdemon3  
**Analysis Date**: October 23, 2025  
**Version**: 3.0.0 (V2 Topic System)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Storage Architecture](#storage-architecture)
7. [API Architecture](#api-architecture)
8. [Frontend Architecture](#frontend-architecture)

---

## System Overview

### What is TikTalk?

TikTalk is a **production-ready, full-stack AI learning platform** that transforms TikTok videos into a searchable, semantically-organized knowledge base. It combines:

- **Video Scraping** - yt-dlp for authenticated TikTok video downloads
- **Speech Transcription** - OpenAI Whisper (faster-whisper) for accurate transcripts
- **Topic Intelligence** - Dual-layer NLP extraction system (V1 + V2)
- **Semantic Search** - FAISS-powered vector search across all content
- **Modern Web UI** - React + TypeScript frontend with cyberpunk aesthetics

### Core Value Proposition

**Transform**: Raw TikTok videos → Structured knowledge  
**Discover**: Semantic search across ideas, not just keywords  
**Learn**: Organize content by topics, categories, and conceptual umbrellas  
**Track**: Idempotent pipeline that only processes new content

### System Scale (Current)

- **Python Backend**: ~10,565 lines of code
- **TypeScript Frontend**: ~8,458 lines of code
- **Total Files**: 69 TypeScript files, 25+ Python modules
- **Data Files**: 182 JSON files across 14 creator accounts
- **Video Coverage**: 100+ transcribed videos
- **Topic Database**: 1,000+ unique topics, 428 canonical topics
- **Search Index**: FAISS vector database with semantic embeddings

---

## Architecture Layers

### Layer 1: Data Ingestion Pipeline

**Purpose**: Fetch, download, transcribe TikTok videos  
**Components**:
- `tiktok_transcriber.py` - Legacy single-video transcriber
- `scripts/ingest_account.py` - Idempotent account ingestion
- `scripts/batch_ingest.py` - Multi-account batch processing
- `core/ingestion_manager.py` - Advanced queue-based ingestion

**Key Features**:
- ✅ **Idempotency**: Only processes new videos (tracked via `index.json`)
- ✅ **Crash Resistance**: Saves after each video
- ✅ **Authentication**: Optional cookies.txt for private/age-restricted content
- ✅ **Speech Detection**: Auto-skips videos with no speech (<50 chars)
- ✅ **Progress Tracking**: Real-time tqdm progress bars
- ✅ **Whisper Modes**: fast/tiny, balanced/small, accurate/medium, ultra/large

**Input**: TikTok username (e.g., @kwrt_)  
**Output**: 
- `accounts/{username}/index.json` - Video metadata and processing status
- `accounts/{username}/transcriptions/{video_id}_transcript.txt` - Full transcripts

### Layer 2: Topic Extraction (Dual System)

**Purpose**: Extract meaningful topics from transcripts using NLP

#### V1 System (Legacy - KeyBERT)
**File**: `topic_extractor.py`  
**Algorithm**: KeyBERT + MaxSum  
**Technology**: SentenceTransformers, NLTK stopwords  
**Output**: `{video_id}_tags.json`, `account_tags.json`, `account_category.json`

**Configuration**:
```python
keyphrase_ngram_range=(1, 3)  # 1-3 word phrases
stop_words='english'
use_maxsum=True
diversity=0.5
top_n=10
```

#### V2 System (Enhanced - MMR + Canonicalization)
**File**: `topic_extractor_v2.py` (595 lines)  
**Algorithm**: spaCy NLP + MMR + Canonicalization  
**Technology**: spaCy (en_core_web_sm), custom MMR implementation  
**Output**: `{video_id}_tags_v2.json` with evidence and confidence scores

**Key Improvements**:
- **spaCy Noun Phrases**: Grammatically correct keyphrase extraction
- **MMR Selection**: λ=0.7 balances relevance vs. redundancy
- **Canonicalization**: Merges similar topics (e.g., "meditate" → "meditation")
- **Timestamped Evidence**: Links topics to specific transcript sentences
- **Confidence Scoring**: 0-1 scale based on MMR score + evidence strength
- **Stop Phrase Filtering**: 60+ generic terms filtered via `config/stop_phrases.txt`

**V2 Data Structure**:
```json
{
  "video_id": "7520122784752700686",
  "username": "kwrt_",
  "total_topics": 10,
  "topics": [
    {
      "tag": "attractiveness",
      "canonical": "attractiveness",
      "confidence": 0.816,
      "score": 0.3959,
      "type": "keyphrase",
      "source": "transcript",
      "evidence": [
        {
          "sentence_index": 30,
          "start": 0.0,
          "end": 0.0,
          "text": "..."
        }
      ],
      "stats": {
        "distinct_sentences": 1,
        "mmr_score": 0.3959
      }
    }
  ]
}
```

### Layer 3: Umbrella Clustering

**Purpose**: Group related topics into semantic meta-topics  
**File**: `umbrella_builder.py` (648 lines)  
**Algorithm**: Louvain community detection (python-louvain + networkx)  
**Alternatives**: Leiden (igraph+leidenalg), HDBSCAN (density-based)

**Process**:
1. **Load Topics**: Gather all canonical topics from account
2. **Embed**: Generate 384-dim embeddings (all-MiniLM-L6-v2)
3. **Build Graph**: Create similarity graph (cosine_sim ≥ 0.7 threshold)
4. **Detect Communities**: Run Louvain algorithm
5. **Label Generation**: Coverage-based algorithm (prioritizes broad terms)
6. **Output**: `topic_umbrellas.json` (max 5 umbrellas per account)

**Label Generation Algorithm**:
```python
# Extract words from all topics in cluster
# Score by coverage: (coverage × 3) + (frequency × 0.5)
# Use single word if coverage ≥ 30%
# Combine 2 complementary words if needed (<50% overlap)
# Proper capitalization for UI
```

**Example Output** (kwrt_):
```json
{
  "umbrella_id": "umbrella_3",
  "label": "Meditation",
  "members": ["meditation isn", "meditate just noisy", ...],
  "member_count": 33,
  "total_frequency": 35,
  "avg_coherence": 0.635,
  "representative_topics": ["meditation isn", "meditate just noisy", ...],
  "video_ids": ["7520323029956709645", ...],
  "stats": {...}
}
```

### Layer 4: Semantic Search

**Purpose**: Vector-based semantic search across all transcripts  
**Directory**: `core/semantic_search/`  
**Technology**: FAISS (Facebook AI Similarity Search) + SentenceTransformers

**Components**:

1. **embedder.py** - `SegmentProcessor`
   - Splits transcripts into semantic segments (sentences/paragraphs)
   - Generates 384-dim embeddings for each segment
   - Extracts timestamps from transcript metadata

2. **storage.py** - `EmbeddingManager`
   - FAISS index management (IndexFlatIP - Inner Product)
   - JSONL metadata storage (parallel to FAISS index)
   - Incremental index building
   - Persistence to `data/search/index.faiss` and `embeddings.jsonl`

3. **engine.py** - `SemanticSearchEngine`
   - Coordinates embedding generation and search
   - Query embedding and similarity scoring
   - Returns ranked results with provenance

4. **timestamp_extractor.py** - `TimestampExtractor`
   - Parses Whisper timestamps from transcripts
   - Maps segments to time ranges
   - Supports multiple timestamp formats

**Search Flow**:
```
User Query → Embed Query → FAISS Search → 
Retrieve Metadata → Score & Filter → Rank Results → 
Return with Snippets + Timestamps
```

**Data Storage**:
- `data/search/index.faiss` - FAISS vector index (~1-10MB)
- `data/search/embeddings.jsonl` - Metadata (username, video_id, text, timestamps)

### Layer 5: REST API

**Purpose**: Expose all functionality via HTTP endpoints  
**File**: `api_server.py` (1,268 lines)  
**Framework**: FastAPI 0.119.1 + Uvicorn 0.24.0  
**Port**: 8000  
**CORS**: Enabled for localhost:5001 (frontend)

**Endpoint Categories**:

1. **Account Management** (6 endpoints)
   - `GET /api/accounts` - List all creators with metadata
   - `GET /api/accounts/{username}/tags` - Account-level topics
   - `GET /api/accounts/{username}/category` - Category classification
   - `GET /api/accounts/{username}/tags/by-video` - Per-video topics
   - `GET /api/accounts/{username}/tags/video/{video_id}` - Single video topics
   - `GET /api/accounts/{username}/umbrellas` - V2 umbrella clusters

2. **Semantic Search** (3 endpoints)
   - `POST /api/search/semantic` - Vector search with filters
   - `GET /api/search/stats` - Index statistics
   - `GET /api/search/filter-options` - Available filter values

3. **Transcript Access** (1 endpoint)
   - `GET /api/transcript/{username}/{video_id}` - Full transcript with highlighting

4. **Ingestion Management** (5 endpoints)
   - `POST /api/ingest/start` - Start bulk ingestion job
   - `GET /api/jobs` - List all jobs
   - `GET /api/jobs/{job_id}` - Job status and progress
   - `POST /api/jobs/{job_id}/pause` - Pause job
   - `POST /api/jobs/{job_id}/cancel` - Cancel job

5. **System Verification** (2 endpoints)
   - `GET /api/verify/system` - Check system health
   - `POST /api/verify/system` - Re-verify system

**Request/Response Models** (Pydantic):
- `SearchRequest`, `SearchResponse`, `SearchFilters`
- `IngestionRequest`, `JobProgress`, `AccountProgress`, `VideoProgress`
- `Tag`, `VideoTags`, `RankedTag`, `AccountTags`, `AccountCategory`
- `UmbrellasResponse`, `EnhancedTopicResponse`

### Layer 6: Frontend UI

**Purpose**: Modern web interface for exploration and search  
**Directory**: `synapse-ai-learning-main/src/`  
**Framework**: React 19 + TypeScript + Vite 6.3.5  
**Port**: 5001  
**Design**: Cyberpunk/neon theme with glass-morphism effects

**Pages** (8 total):

1. **DashboardPage.tsx** - System overview and quick stats
2. **LibraryPage.tsx** - Browse all creators with category badges
3. **CreatorDetailPage.tsx** - 3 tabs:
   - Topics: All extracted topics with frequency
   - Categories: 15-category confidence scores
   - Umbrellas: V2 semantic clusters with badges
4. **SearchPage.tsx** - Semantic search with advanced filters
5. **TranscriptsPage.tsx** - Browse transcripts with V2 banner
6. **TranscriptPage.tsx** - Individual transcript view with highlights
7. **IngestPage.tsx** - Bulk ingestion UI with real-time progress
8. **LoginPage.tsx** - Authentication (future)

**Key UI Components** (30+ total):
- `SearchResultCard` - Result display with snippets
- `SearchFilters` - Advanced filter panel
- `TranscriptViewer` - Transcript display with highlighting
- `IngestionProgress` - Real-time job progress
- `EmptyState` - Graceful empty states
- `CategoryBadge` - Visual category indicators

**State Management**:
- React Query (@tanstack/react-query) for server state
- GitHub Spark hooks (@github/spark) for local storage
- React Router for navigation

**Styling**:
- Tailwind CSS 4.1.11
- Custom cyberpunk theme (`theme.json`)
- Glass-morphism effects
- Neon glow animations
- Responsive design

---

## Technology Stack

### Backend Technologies

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | Python | 3.9+ | Core language |
| **Video Processing** | yt-dlp | 2023.12.30+ | TikTok video downloads |
| **Transcription** | faster-whisper | 1.2.0 | OpenAI Whisper inference |
| **Audio Processing** | ffmpeg-python | 0.2.0+ | Audio extraction |
| **NLP - V1** | KeyBERT | 0.9.0 | Keyphrase extraction |
| **NLP - V2** | spaCy | 3.8.7 | Advanced NLP |
| **Embeddings** | sentence-transformers | 5.1.1 | Semantic embeddings |
| **ML Framework** | scikit-learn | 1.3.0+ | ML utilities |
| **Text Processing** | NLTK | 3.9.2 | Stopwords, tokenization |
| **Clustering** | python-louvain | 0.16 | Community detection |
| **Graph** | networkx | 3.5 | Graph structures |
| **Vector Search** | faiss-cpu | 1.12.0 | Similarity search |
| **Web Framework** | FastAPI | 0.119.1 | REST API |
| **Server** | Uvicorn | 0.24.0 | ASGI server |
| **Data Processing** | pandas | 2.1.4+ | DataFrames |
| **Math** | numpy | 1.24.4+ | Numerical computing |

### Frontend Technologies

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Language** | TypeScript | 5.7.2 | Type-safe JavaScript |
| **Framework** | React | 19.0.0 | UI framework |
| **Build Tool** | Vite | 6.3.5 | Fast dev server + bundler |
| **Routing** | React Router | 7.9.4 | Client-side routing |
| **State Management** | React Query | 5.83.1 | Server state |
| **Styling** | Tailwind CSS | 4.1.11 | Utility-first CSS |
| **UI Components** | Radix UI | Various | Accessible primitives |
| **Icons** | Phosphor Icons | 2.1.7 | Icon library |
| **Animations** | Framer Motion | 12.6.2 | Animations |
| **Toast** | Sonner | 2.0.1 | Notifications |
| **Forms** | React Hook Form | 7.54.2 | Form management |
| **Validation** | Zod | 3.25.76 | Schema validation |

### Development Tools

- **Python Environment**: pip, virtualenv
- **Node Environment**: npm, node 18+
- **Version Control**: Git
- **Process Management**: nohup, background processes
- **Testing**: pytest (planned), jest (planned)

---

## Core Components

### 1. IdempotentIngestionManager

**File**: `scripts/ingest_account.py`  
**Purpose**: Manages idempotent video ingestion  
**Lines**: 374

**Key Methods**:
- `__init__(username, base_dir)` - Initialize with username
- `_load_index()` - Load or create index.json
- `_save_index()` - Persist index.json
- `get_processed_video_ids()` - Get set of processed IDs
- `filter_new_videos(all_videos)` - Filter out already-processed
- `mark_video_processed(video_id, metadata, success)` - Update index
- `ingest_account(...)` - Main ingestion orchestrator

**Index Structure**:
```json
{
  "account": "kwrt_",
  "created_at": "2025-10-21T07:30:00",
  "last_updated": "2025-10-21T08:15:00",
  "processed_videos": {
    "7557947251092409613": {
      "video_id": "7557947251092409613",
      "title": "#philosophy #wisdom #life",
      "processed_at": "2025-10-21T07:30:15",
      "success": true,
      "transcript_file": "7557947251092409613_transcript.txt",
      "transcription_length": 5298,
      "duration": 337,
      "url": "https://www.tiktok.com/@kwrt_/video/7557947251092409613"
    }
  },
  "stats": {
    "total_videos_found": 15,
    "total_processed": 10,
    "total_skipped": 2,
    "total_failed": 0,
    "last_ingestion_date": "2025-10-21T08:15:00"
  }
}
```

### 2. TopicExtractorV2

**File**: `topic_extractor_v2.py`  
**Purpose**: Enhanced topic extraction with evidence  
**Lines**: 595

**Key Methods**:
- `__init__(model_name, spacy_model, config_dir)` - Initialize models
- `_load_canonical_topics()` - Load canonicalization rules
- `_load_stop_phrases()` - Load stop phrase filter
- `_extract_noun_phrases(text)` - spaCy noun phrase extraction
- `_compute_mmr(embeddings, candidates, lambda_param)` - MMR selection
- `_canonicalize(topic)` - Merge similar topics
- `_find_evidence(topic, transcript, sentences, timestamps)` - Extract evidence
- `_compute_confidence(mmr_score, evidence_count, frequency)` - Confidence scoring
- `extract_video_topics_enhanced(video_id, username, transcript, ...)` - Main V2 extraction
- `extract_account_topics_v2(username, force)` - Process all videos in account

**MMR Formula**:
```python
# λ * relevance - (1-λ) * max_similarity_to_selected
# λ=0.7 (70% relevance, 30% diversity)
mmr_score = lambda_param * relevance - (1 - lambda_param) * redundancy
```

**Confidence Scoring**:
```python
# Normalize MMR score [-0.5, 0.7] → [0, 1]
normalized_mmr = (mmr_score + 0.5) / 1.2

# Evidence boost (up to +0.3)
evidence_boost = min(0.3, np.log1p(evidence_count) / 10)

# Final confidence
confidence = min(1.0, normalized_mmr + evidence_boost)
```

### 3. UmbrellaBuilder

**File**: `umbrella_builder.py`  
**Purpose**: Cluster topics into semantic umbrellas  
**Lines**: 648

**Key Methods**:
- `__init__(similarity_threshold, min_cluster_size, model_name)` - Initialize
- `build_account_umbrellas(username, max_umbrellas, force)` - Main builder
- `_load_canonical_topics(username)` - Load V2 topics
- `_embed_topics(topics)` - Generate embeddings
- `_build_similarity_graph(topics, embeddings, threshold)` - Create graph
- `_cluster_louvain(graph)` - Louvain community detection
- `_cluster_leiden(graph)` - Leiden algorithm (alternative)
- `_cluster_hdbscan(embeddings)` - HDBSCAN (fallback)
- `_generate_umbrella_label(topics, embeddings)` - Label generation
- `_compute_cluster_stats(cluster_topics, cluster_embeddings)` - Statistics

**Label Generation Algorithm**:
```python
# 1. Extract words from all topics
word_counts = defaultdict(int)
word_topics = defaultdict(set)

# 2. Filter stopwords + video terms
stopwords = {'the', 'a', 'video', 'watching', 'thank', ...}

# 3. Score by coverage (not frequency)
coverage = len(word_topics[word]) / len(cluster_topics)
word_score = (coverage × 3) + (frequency × 0.5)

# 4. Use single word if coverage ≥ 30%
if coverage >= 0.3:
    return top_word.capitalize()

# 5. Combine 2 complementary words
overlap = len(topics1 & topics2) / min(len(topics1), len(topics2))
if overlap < 0.5:
    return f"{word1.capitalize()} {word2.capitalize()}"
```

### 4. SemanticSearchEngine

**File**: `core/semantic_search/engine.py`  
**Purpose**: Coordinate semantic search operations  
**Lines**: 270

**Key Methods**:
- `__init__(model_name, index_path, metadata_path)` - Initialize
- `process_transcript(transcript, video_id, username)` - Add to index
- `search(query, top_k)` - Perform semantic search
- `_create_snippet(text)` - Generate 2-3 sentence snippet
- `rebuild_index()` - Rebuild FAISS index from scratch

**Search Process**:
```python
# 1. Embed query
query_embedding = model.encode(query)

# 2. FAISS search
distances, indices = faiss_index.search(query_embedding, top_k)

# 3. Retrieve metadata
results = [metadata[i] for i in indices]

# 4. Score and filter
results = [r for r in results if r['score'] >= min_score]

# 5. Apply filters (username, category, tags, dates)
results = apply_filters(results, filters)

# 6. Sort (relevance, recency, timestamp)
results = sort_results(results, sort_by)

return results
```

### 5. IngestionManager (Advanced Queue)

**File**: `core/ingestion_manager.py`  
**Purpose**: Advanced bulk ingestion with queue management  
**Lines**: 744

**Key Features**:
- **Asynchronous**: Uses asyncio for concurrent operations
- **Queue System**: Job queue with status tracking
- **Progress Tracking**: Real-time progress per video and account
- **Filtering**: Advanced video filtering (date, count, history segment, tags)
- **Pause/Resume**: Job control capabilities
- **Automatic V2**: Calls V2 extractor and umbrella builder automatically

**Data Classes**:
```python
@dataclass
class VideoFilter:
    last_n_videos: Optional[int] = None
    percentage: Optional[float] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    history_start: Optional[float] = None  # 0.0-1.0
    history_end: Optional[float] = None
    only_with_speech: bool = False
    skip_no_speech: bool = True
    required_tags: Optional[List[str]] = None
    required_category: Optional[str] = None

@dataclass
class IngestionSettings:
    whisper_mode: str = "balanced"  # fast, balanced, accurate, ultra
    skip_existing: bool = True
    retranscribe_low_confidence: bool = False
    max_duration_minutes: Optional[int] = None

@dataclass
class VideoProgress:
    video_id: str
    title: str
    status: IngestionStatus  # queued, downloading, transcribing, etc.
    step: Optional[str] = None
    progress: float = 0.0  # 0-100
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class AccountProgress:
    username: str
    status: IngestionStatus
    total_videos: int = 0
    filtered_videos: int = 0
    processed_videos: int = 0
    skipped_videos: int = 0
    failed_videos: int = 0
    overall_progress: float = 0.0
    current_video: Optional[VideoProgress] = None
    videos: Optional[List[VideoProgress]] = None
```

**Ingestion Flow**:
```
1. QUEUED → 2. FETCHING_METADATA → 3. FILTERING → 
4. DOWNLOADING → 5. TRANSCRIBING → 6. EXTRACTING_TOPICS (V1) →
7. EXTRACTING_TOPICS (V2) → 8. EMBEDDING → 9. COMPLETE
```

**V2 Integration** (Lines 650-710):
```python
# After V1 extraction
self.update_job_status(job_id, IngestionStatus.EXTRACTING_TOPICS, 
    step="Extracting topics (V1)...")
extract_all_topics(username)

# V2 extraction
self.update_job_status(job_id, IngestionStatus.EXTRACTING_TOPICS,
    step="Extracting topics (V2)...")
TopicExtractorV2().extract_account_topics_v2(username, force=False)

# Umbrella building
self.update_job_status(job_id, IngestionStatus.EXTRACTING_TOPICS,
    step="Building topic umbrellas...")
UmbrellaBuilder().build_account_umbrellas(username, max_umbrellas=5)
```

---

## Data Flow

### Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                                       │
│    - TikTok username (@kwrt_)                                      │
│    - Video filters (last N, date range, etc.)                     │
│    - Whisper mode (fast/balanced/accurate/ultra)                  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. VIDEO SCRAPING (yt-dlp)                                         │
│    - Fetch video metadata from TikTok                              │
│    - Filter by criteria (date, count, speech)                     │
│    - Download video files (mp4)                                    │
│    - Extract audio (ffmpeg)                                        │
│    Output: accounts/{user}/videos/*.mp4 (temp)                    │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. TRANSCRIPTION (faster-whisper)                                  │
│    - Load Whisper model (tiny/small/medium/large)                 │
│    - Transcribe audio to text                                      │
│    - Extract timestamps for each segment                           │
│    - Detect language and confidence                                │
│    Output: accounts/{user}/transcriptions/{video_id}_transcript.txt│
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. INDEX UPDATE                                                     │
│    - Mark video as processed in index.json                         │
│    - Store metadata (title, duration, url)                         │
│    - Update stats (total processed, failed, etc.)                  │
│    Output: accounts/{user}/index.json                              │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. TOPIC EXTRACTION V1 (KeyBERT)                                   │
│    - Load transcript                                                │
│    - Extract 1-3 word keyphrases                                   │
│    - Score by semantic relevance                                   │
│    - Apply diversity (MaxSum)                                      │
│    - Filter stopwords                                              │
│    Output: accounts/{user}/topics/{video_id}_tags.json            │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. TOPIC EXTRACTION V2 (spaCy + MMR)                              │
│    - Extract noun phrases with spaCy                               │
│    - Apply MMR for diversity (λ=0.7)                              │
│    - Canonicalize topics (meditation = meditate)                  │
│    - Find timestamped evidence                                     │
│    - Compute confidence scores                                     │
│    Output: accounts/{user}/topics/{video_id}_tags_v2.json         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. ACCOUNT AGGREGATION                                              │
│    - Collect all topics from all videos                            │
│    - Count frequency (how many videos mention each)                │
│    - Calculate average scores                                       │
│    - Rank by combined_score                                        │
│    Output: accounts/{user}/topics/account_tags.json                │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 8. CATEGORY CLASSIFICATION                                          │
│    - Aggregate all transcripts                                      │
│    - Generate semantic embedding                                    │
│    - Compare against 15 category embeddings                        │
│    - Calculate cosine similarity scores                            │
│    - Select highest-scoring category                               │
│    Output: accounts/{user}/topics/account_category.json            │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 9. UMBRELLA CLUSTERING                                              │
│    - Load all canonical topics                                      │
│    - Generate embeddings for each topic                            │
│    - Build similarity graph (threshold=0.7)                        │
│    - Run Louvain community detection                               │
│    - Generate labels (coverage-based algorithm)                    │
│    - Limit to top 5 umbrellas by member count                     │
│    Output: accounts/{user}/topics/topic_umbrellas.json             │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 10. SEMANTIC EMBEDDING                                              │
│     - Split transcript into semantic segments                      │
│     - Generate 384-dim embeddings per segment                      │
│     - Extract timestamps for each segment                          │
│     - Add to FAISS index                                           │
│     - Store metadata in JSONL                                      │
│     Output: data/search/index.faiss, embeddings.jsonl             │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 11. API EXPOSURE                                                    │
│     - FastAPI serves all data via REST endpoints                   │
│     - CORS enabled for frontend                                    │
│     - Pydantic models for validation                               │
│     - Real-time job progress tracking                              │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 12. FRONTEND DISPLAY                                                │
│     - React UI fetches data from API                               │
│     - Display creators, topics, categories                         │
│     - Semantic search interface                                    │
│     - Real-time ingestion progress                                 │
│     - Transcript viewer with highlights                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Transformation Example

**Input** (TikTok URL):
```
https://www.tiktok.com/@kwrt_/video/7520122784752700686
```

**Step 1 - Transcript**:
```text
Looks maxing fucking sucks... Being attractive does come with 
a lot of benefits... But since when was the only fucking point 
of life external validation?... Loneliness is a lack of love... 
These are things you can give to yourself...
```

**Step 2 - V1 Topics**:
```json
["attractiveness", "ego attractiveness", "solitude loneliness"]
```

**Step 3 - V2 Enhanced Topics**:
```json
{
  "tag": "attractiveness",
  "canonical": "attractiveness",
  "confidence": 0.816,
  "evidence": [
    {
      "sentence_index": 30,
      "text": "...status and ego and attractiveness..."
    }
  ]
}
```

**Step 4 - Account Aggregation**:
```json
{
  "tag": "attractiveness",
  "frequency": 3,  // appears in 3 videos
  "avg_score": 0.45,
  "combined_score": 1.35
}
```

**Step 5 - Category**:
```json
{
  "category": "Spirituality",
  "confidence": 0.531
}
```

**Step 6 - Umbrella**:
```json
{
  "umbrella_id": "umbrella_26",
  "label": "Identity",
  "members": ["attractiveness", "ego attractiveness", "status ego attractiveness"]
}
```

**Step 7 - Search Index**:
```
Segment 1: "Looks maxing fucking sucks..." [embedding: [0.12, -0.45, ...]]
Segment 2: "Being attractive does come..." [embedding: [0.34, 0.12, ...]]
```

**Result**: Searchable via semantic query "physical appearance and ego"

---

## Storage Architecture

### Directory Structure

```
TikTalk/
├── accounts/                          # All account data
│   ├── _batch_reports/               # CSV batch ingestion reports
│   └── {username}/                   # Per-creator directory
│       ├── index.json               # Video metadata + processing status
│       ├── transcriptions/          # Raw transcripts
│       │   ├── {video_id}_transcript.txt
│       │   └── {username}_results.json  # Legacy results
│       └── topics/                  # Topic extraction outputs
│           ├── {video_id}_tags.json      # V1 topics
│           ├── {video_id}_tags_v2.json   # V2 topics (enhanced)
│           ├── account_tags.json         # Aggregated topics
│           ├── account_category.json     # Category classification
│           └── topic_umbrellas.json      # Semantic umbrellas
│
├── config/                            # Configuration files
│   ├── canonical_topics.json        # Topic merge rules
│   └── stop_phrases.txt             # Generic phrase filters
│
├── core/                              # Core pipeline modules
│   ├── ingestion_manager.py         # Advanced ingestion queue
│   └── semantic_search/             # Search subsystem
│       ├── embedder.py              # Segment processing
│       ├── engine.py                # Search coordination
│       ├── storage.py               # FAISS index management
│       └── timestamp_extractor.py   # Timestamp parsing
│
├── data/                              # Generated data
│   └── search/                       # Search index
│       ├── index.faiss              # FAISS vector index
│       └── embeddings.jsonl         # Segment metadata
│
├── scripts/                           # Utility scripts
│   ├── ingest_account.py            # Single account ingestion
│   ├── batch_ingest.py              # Multi-account batch
│   ├── extract_topics.py            # Topic extraction CLI
│   ├── list_topics.py               # View topics
│   ├── search_semantic.py           # CLI semantic search
│   ├── show_transcript.py           # View transcripts
│   ├── verify_ingestion.py          # Data integrity check
│   └── migrate_topics_v2.py         # V1→V2 migration
│
├── synapse-ai-learning-main/          # Frontend application
│   ├── src/
│   │   ├── components/              # Reusable UI components
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── lib/                     # Utilities and API client
│   │   ├── pages/                   # Page components
│   │   └── styles/                  # CSS and themes
│   ├── dist/                         # Production build
│   ├── package.json                  # Dependencies
│   ├── vite.config.ts               # Vite configuration
│   └── tsconfig.json                # TypeScript config
│
├── api_server.py                      # FastAPI REST server
├── tiktok_transcriber.py              # Legacy transcriber
├── topic_extractor.py                 # V1 topic extraction
├── topic_extractor_v2.py              # V2 enhanced extraction
├── umbrella_builder.py                # Umbrella clustering
├── requirements.txt                   # Python dependencies
└── README.md                          # Documentation
```

### File Formats

#### 1. Transcript File
**Path**: `accounts/{user}/transcriptions/{video_id}_transcript.txt`
```text
# Transcription for Video 7520122784752700686
Title: taking the redpill #redpilltiktok #men #looksmax #masculinity #matrix
Timestamp: 2025-10-21T07:30:15
==================================================

[Full transcript text here...]
```

#### 2. Index File
**Path**: `accounts/{user}/index.json`
```json
{
  "account": "kwrt_",
  "created_at": "2025-10-21T07:30:00",
  "last_updated": "2025-10-21T08:15:00",
  "processed_videos": {
    "{video_id}": {
      "video_id": "...",
      "title": "...",
      "processed_at": "...",
      "success": true,
      "transcript_file": "...",
      "transcription_length": 5298,
      "duration": 337,
      "url": "..."
    }
  },
  "stats": {
    "total_videos_found": 15,
    "total_processed": 10,
    "total_skipped": 2,
    "total_failed": 0
  }
}
```

#### 3. V2 Topic File
**Path**: `accounts/{user}/topics/{video_id}_tags_v2.json`
```json
{
  "video_id": "...",
  "username": "...",
  "title": "...",
  "total_topics": 10,
  "topics": [
    {
      "tag": "attractiveness",
      "canonical": "attractiveness",
      "confidence": 0.816,
      "score": 0.3959,
      "type": "keyphrase",
      "source": "transcript",
      "evidence": [
        {
          "sentence_index": 30,
          "start": 0.0,
          "end": 0.0,
          "text": "..."
        }
      ],
      "stats": {
        "distinct_sentences": 1,
        "mmr_score": 0.3959
      }
    }
  ]
}
```

#### 4. Umbrella File
**Path**: `accounts/{user}/topics/topic_umbrellas.json`
```json
{
  "username": "kwrt_",
  "total_topics": 429,
  "canonical_topics": 428,
  "umbrella_count": 5,
  "total_clusters": 81,
  "clustering_method": "louvain",
  "similarity_threshold": 0.7,
  "umbrellas": [
    {
      "umbrella_id": "umbrella_3",
      "label": "Meditation",
      "members": ["meditation isn", "meditate just noisy", ...],
      "member_count": 33,
      "total_frequency": 35,
      "avg_coherence": 0.635,
      "representative_topics": [...],
      "video_ids": [...],
      "stats": {...}
    }
  ]
}
```

#### 5. FAISS Index
**Path**: `data/search/index.faiss`
- Binary file containing vector index
- IndexFlatIP (Inner Product similarity)
- 384 dimensions per vector
- Typically 1-10MB depending on corpus size

#### 6. Embeddings Metadata
**Path**: `data/search/embeddings.jsonl`
```json
{"text": "...", "video_id": "...", "username": "...", "timestamp": "...", "start_time": 0.0, "end_time": 5.2, "segment_id": 0}
{"text": "...", "video_id": "...", "username": "...", "timestamp": "...", "start_time": 5.2, "end_time": 10.5, "segment_id": 1}
```

### Storage Scaling

| Data Type | Size per Video | Size per Account (50 videos) | Notes |
|-----------|----------------|------------------------------|-------|
| Raw Video | 5-20 MB | 250-1000 MB | Temporary (deleted after transcription) |
| Transcript | 2-10 KB | 100-500 KB | Plain text |
| V1 Topics | 1-2 KB | 50-100 KB | JSON |
| V2 Topics | 3-5 KB | 150-250 KB | JSON with evidence |
| Embeddings | 10-50 KB | 500KB-2.5MB | JSONL + FAISS |
| Total per Account | ~15-75 KB | ~800KB-3MB | Excluding videos |

**Current System** (14 accounts, ~150 videos):
- Transcripts: ~1.5 MB
- Topics: ~2 MB
- Search Index: ~3 MB
- **Total**: ~6.5 MB

---

## API Architecture

### Endpoint Categories

#### 1. Account Management

```
GET /api/accounts
└── Returns: List of all creators with metadata

GET /api/accounts/{username}/tags?top_n=20&min_frequency=2
└── Returns: Account-level ranked topics

GET /api/accounts/{username}/category
└── Returns: Category classification with confidence

GET /api/accounts/{username}/tags/by-video
└── Returns: Per-video topic breakdown

GET /api/accounts/{username}/tags/video/{video_id}
└── Returns: Topics for specific video

GET /api/accounts/{username}/umbrellas
└── Returns: V2 semantic umbrella clusters
```

#### 2. Semantic Search

```
POST /api/search/semantic
Body: {
  "query": "meditation and consciousness",
  "top_k": 200,
  "filters": {
    "usernames": ["kwrt_", "matrix.v5"],
    "category": "Spirituality",
    "tags": ["meditation"],
    "min_score": 0.15,
    "date_from": "2025-01-01",
    "date_to": "2025-12-31"
  },
  "sort": "relevance"  // relevance, recency, timestamp
}
└── Returns: Ranked search results with snippets

GET /api/search/stats
└── Returns: Index statistics (total segments, accounts, etc.)

GET /api/search/filter-options
└── Returns: Available filter values (usernames, categories, tags)
```

#### 3. Transcript Access

```
GET /api/transcript/{username}/{video_id}?query=meditation&highlights=5
└── Returns: Full transcript with optional highlighting

Query Parameters:
- query: Search query for highlighting
- highlights: Number of highlights to include
```

#### 4. Ingestion Management

```
POST /api/ingest/start
Body: {
  "usernames": ["kwrt_", "matrix.v5"],
  "filters": {
    "last_n_videos": 50,
    "date_from": "2025-01-01",
    "only_with_speech": true
  },
  "settings": {
    "whisper_mode": "balanced",
    "skip_existing": true
  }
}
└── Returns: {job_id, status, message}

GET /api/jobs
└── Returns: List of all ingestion jobs

GET /api/jobs/{job_id}
└── Returns: Detailed job progress

POST /api/jobs/{job_id}/pause
└── Pauses running job

POST /api/jobs/{job_id}/cancel
└── Cancels job

POST /api/jobs/{job_id}/resume
└── Resumes paused job
```

#### 5. System Verification

```
GET /api/verify/system
└── Returns: System health check

POST /api/verify/system
└── Re-verifies system and returns status
```

### Request/Response Examples

#### Semantic Search Request
```json
POST /api/search/semantic
{
  "query": "meditation and mindfulness practices",
  "top_k": 200,
  "filters": {
    "usernames": ["kwrt_"],
    "category": "Spirituality",
    "min_score": 0.15
  },
  "sort": "relevance"
}
```

#### Semantic Search Response
```json
{
  "query": "meditation and mindfulness practices",
  "total_results": 12,
  "results": [
    {
      "text": "Full segment text...",
      "snippet": "...focused on meditation...",
      "video_id": "7520122784752700686",
      "username": "kwrt_",
      "timestamp": "2025-10-21T07:30:15",
      "start_time": 12.5,
      "end_time": 18.3,
      "score": 0.847,
      "segment_id": 3
    }
  ]
}
```

#### Ingestion Request
```json
POST /api/ingest/start
{
  "usernames": ["kwrt_"],
  "filters": {
    "last_n_videos": 50,
    "only_with_speech": true
  },
  "settings": {
    "whisper_mode": "balanced"
  }
}
```

#### Ingestion Progress Response
```json
GET /api/jobs/{job_id}
{
  "job_id": "abc123",
  "status": "transcribing",
  "accounts": [
    {
      "username": "kwrt_",
      "status": "transcribing",
      "total_videos": 50,
      "filtered_videos": 45,
      "processed_videos": 12,
      "overall_progress": 26.7,
      "current_video": {
        "video_id": "7520122784752700686",
        "title": "...",
        "status": "transcribing",
        "progress": 65.0
      }
    }
  ],
  "started_at": "2025-10-23T10:30:00",
  "estimated_completion": "2025-10-23T11:15:00"
}
```

---

## Frontend Architecture

### Component Hierarchy

```
App.tsx
├── Router
│   ├── DashboardPage.tsx
│   │   ├── SystemStats
│   │   ├── RecentActivity
│   │   └── QuickActions
│   │
│   ├── LibraryPage.tsx
│   │   ├── CreatorGrid
│   │   │   └── CreatorCard (x N)
│   │   ├── SearchBar
│   │   └── FilterPanel
│   │
│   ├── CreatorDetailPage.tsx
│   │   ├── Tabs
│   │   │   ├── TopicsTab
│   │   │   │   └── TopicBadges
│   │   │   ├── CategoriesTab
│   │   │   │   └── CategoryCards
│   │   │   └── UmbrellasTab (V2)
│   │   │       └── UmbrellaCards
│   │   └── BackButton
│   │
│   ├── SearchPage.tsx
│   │   ├── SearchBar
│   │   ├── SearchFilters
│   │   │   ├── UsernameFilter
│   │   │   ├── CategoryFilter
│   │   │   ├── TagFilter
│   │   │   └── DateFilter
│   │   └── SearchResults
│   │       └── SearchResultCard (x N)
│   │
│   ├── TranscriptsPage.tsx
│   │   ├── V2Banner
│   │   ├── TranscriptList
│   │   │   └── TranscriptCard (x N)
│   │   └── FilterControls
│   │
│   ├── TranscriptPage.tsx
│   │   ├── VideoMeta
│   │   ├── TranscriptViewer
│   │   │   ├── HighlightedText
│   │   │   └── TimestampLinks
│   │   └── TopicTags
│   │
│   └── IngestPage.tsx
│       ├── IngestionForm
│       │   ├── UsernameInput
│       │   ├── FilterOptions
│       │   └── SettingsPanel
│       ├── JobList
│       │   └── JobCard (x N)
│       └── ProgressTracker
│           ├── AccountProgress
│           └── VideoProgress
│
└── ErrorBoundary
```

### State Management

#### Server State (React Query)
```typescript
// Custom hooks for API data
useCreators() → GET /api/accounts
useCreatorTags(username) → GET /api/accounts/{username}/tags
useCreatorCategories(username) → GET /api/accounts/{username}/category
useUmbrellas(username) → GET /api/accounts/{username}/umbrellas
useSemanticSearch(query, filters) → POST /api/search/semantic
useTranscript(username, videoId) → GET /api/transcript/{username}/{videoId}
useJobs() → GET /api/jobs
useJobStatus(jobId) → GET /api/jobs/{jobId}
```

#### Local State (GitHub Spark KV)
```typescript
// Persisted in localStorage
useKV('recent-searches', []) → Recent search queries
useKV('search-filters', {}) → Last used filters
useKV('theme-preference', 'dark') → UI theme
useKV('view-mode', 'grid') → Grid/list view preference
```

#### Component State (useState)
```typescript
// Ephemeral state
const [isLoading, setIsLoading] = useState(false)
const [selectedTags, setSelectedTags] = useState<string[]>([])
const [filtersOpen, setFiltersOpen] = useState(false)
```

### Routing

```typescript
// React Router v7 configuration
<Routes>
  <Route path="/" element={<DashboardPage />} />
  <Route path="/library" element={<LibraryPage />} />
  <Route path="/creator/:username" element={<CreatorDetailPage />} />
  <Route path="/search" element={<SearchPage />} />
  <Route path="/transcripts" element={<TranscriptsPage />} />
  <Route path="/transcript/:username/:videoId" element={<TranscriptPage />} />
  <Route path="/ingest" element={<IngestPage />} />
  <Route path="/login" element={<LoginPage />} />
  <Route path="*" element={<NotFound />} />
</Routes>
```

### Styling System

#### Tailwind Configuration
```javascript
// tailwind.config.js
theme: {
  extend: {
    colors: {
      'electric-purple': '#a78bfa',
      'hot-pink': '#fb7185',
      'neon-blue': '#3b82f6',
      'cyber-green': '#10b981',
      'dark-void': '#0a0a0f',
      'glass-bg': 'rgba(255, 255, 255, 0.05)'
    },
    backdropBlur: {
      'glass': '10px'
    }
  }
}
```

#### Custom CSS Classes
```css
/* Glass morphism */
.glass-panel {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Neon glow */
.neon-glow {
  box-shadow: 0 0 20px rgba(167, 139, 250, 0.5);
}

.neon-glow-hover:hover {
  box-shadow: 0 0 30px rgba(167, 139, 250, 0.8);
  transform: translateY(-2px);
  transition: all 0.3s ease;
}

/* Gradient text */
.gradient-text {
  background: linear-gradient(to right, #a78bfa, #fb7185);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Performance Optimizations

1. **Code Splitting**
   - Lazy loading of route components
   - Dynamic imports for heavy libraries

2. **Memoization**
   - React.memo for expensive components
   - useMemo for computed values
   - useCallback for stable function references

3. **Virtual Scrolling**
   - Large lists use windowing (planned)
   - Infinite scroll for search results

4. **Debouncing**
   - Search input debounced (300ms)
   - Filter changes debounced (500ms)

5. **Caching**
   - React Query cache (5 min default)
   - Service worker for assets (planned)

---

*Document 1 of 3 - Continue to FEATURES_AND_CAPABILITIES.md*
