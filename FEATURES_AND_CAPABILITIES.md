# TikTalk Features & Capabilities Deep Dive

**Repository**: TikTalk  
**Analysis Date**: October 23, 2025  
**Document**: 2 of 3

---

## Table of Contents

1. [Core Features](#core-features)
2. [Topic System V1 vs V2](#topic-system-v1-vs-v2)
3. [Semantic Search Capabilities](#semantic-search-capabilities)
4. [Ingestion Features](#ingestion-features)
5. [UI/UX Features](#ui-ux-features)
6. [Data Quality Features](#data-quality-features)
7. [Advanced Capabilities](#advanced-capabilities)
8. [Limitations & Constraints](#limitations--constraints)

---

## Core Features

### 1. Video Transcription

**Technology**: OpenAI Whisper via faster-whisper  
**Accuracy**: Industry-leading speech-to-text  
**Languages**: 99 languages supported  
**Speed**: GPU accelerated (when available)

**Whisper Modes**:

| Mode | Model Size | Speed | Accuracy | Use Case |
|------|-----------|-------|----------|----------|
| **fast** | tiny (39M params) | ~1x realtime | Good | Quick processing, testing |
| **balanced** | small (244M params) | ~2x realtime | Better | Production default |
| **accurate** | medium (769M params) | ~4x realtime | Best | High-quality content |
| **ultra** | large (1550M params) | ~8x realtime | Perfect | Critical transcription |

**Features**:
- ✅ Automatic language detection
- ✅ Timestamp extraction per word/segment
- ✅ Confidence scoring per segment
- ✅ Speaker diarization (planned)
- ✅ Punctuation and capitalization
- ✅ Background noise handling
- ✅ Music/speech separation

**Speech Detection**:
```python
# Auto-skip videos with minimal speech
min_speech_threshold = 50  # characters
if len(transcript) < min_speech_threshold:
    skip_video()
```

**Output Format**:
```text
# Transcription for Video 7520122784752700686
Title: taking the redpill #redpilltiktok #men #looksmax #masculinity #matrix
Timestamp: 2025-10-21T07:30:15
Duration: 337 seconds
Model: small
Language: English (en)
Confidence: 0.95
==================================================

[0.0s - 5.2s] Looks maxing fucking sucks...
[5.2s - 10.5s] Being attractive does come with a lot of benefits...
[10.5s - 15.8s] But since when was the only fucking point of life external validation?...
```

### 2. Idempotent Pipeline

**Core Principle**: Only process what's new, skip what exists

**Implementation**:
- `index.json` tracks all processed videos
- Each run checks processed_videos before downloading
- Crash-safe: saves after each video
- Resumable: can restart failed ingestions

**Benefits**:
- 💰 **Cost Savings**: Don't re-download/re-transcribe
- ⚡ **Speed**: Skip existing work instantly
- 🛡️ **Reliability**: Never lose progress
- 🔄 **Incremental**: Update accounts with new videos only

**Example**:
```bash
# First run - processes 50 videos (takes 2 hours)
python scripts/ingest_account.py --user kwrt_ --max-videos 50

# Second run - skips 50, processes only new 5 videos (takes 10 minutes)
python scripts/ingest_account.py --user kwrt_ --max-videos 55
```

**Statistics Tracking**:
```json
{
  "stats": {
    "total_videos_found": 55,
    "total_processed": 55,
    "total_skipped": 50,  // Already done!
    "total_failed": 0,
    "last_ingestion_date": "2025-10-23T14:30:00"
  }
}
```

### 3. Dual-Layer Topic System

**Philosophy**: Two complementary approaches for maximum insight

#### Layer 1: Broad Categories (15 predefined)

**Purpose**: High-level content classification  
**Method**: Semantic embedding comparison  
**Output**: Single category with confidence score

**Categories**:
1. **Philosophy** - Abstract thinking, existentialism, meaning
2. **Spirituality** - Meditation, consciousness, awakening
3. **Self-Improvement** - Personal growth, habits, productivity
4. **Psychology** - Human behavior, mental models, cognition
5. **Business** - Entrepreneurship, strategy, leadership
6. **Health** - Fitness, nutrition, wellness, medicine
7. **Tech** - Technology, programming, innovation, AI
8. **Politics** - Government, policy, social issues
9. **History** - Historical events, context, analysis
10. **Creativity** - Art, design, creative process
11. **Education** - Teaching, learning, pedagogy
12. **Entertainment** - Comedy, storytelling, pop culture
13. **Music** - Musical theory, performance, composition
14. **Art** - Visual arts, aesthetics, craft
15. **Science** - Research, experiments, discoveries

**Classification Process**:
```python
# 1. Aggregate all transcripts for creator
combined_text = "\n".join(all_transcripts)

# 2. Generate embedding
creator_embedding = model.encode(combined_text)

# 3. Compare against category embeddings
for category in CATEGORIES:
    category_embedding = model.encode(category_description)
    similarity = cosine_similarity(creator_embedding, category_embedding)
    scores[category] = similarity

# 4. Select winner
primary_category = max(scores, key=scores.get)
confidence = scores[primary_category]
```

**Example Output**:
```json
{
  "category": "Spirituality",
  "confidence": 0.531,
  "all_scores": {
    "Spirituality": 0.531,
    "Philosophy": 0.464,
    "Psychology": 0.453,
    "Self-Improvement": 0.443,
    ...
  }
}
```

#### Layer 2: Granular Topics (Dynamic)

**Purpose**: Fine-grained topic extraction per video  
**Method**: KeyBERT (V1) + spaCy+MMR (V2)  
**Output**: 3-10 topics per video, aggregated at account level

**V1 Topics** (KeyBERT + MaxSum):
- 1-3 word keyphrases
- Semantic relevance scoring
- Diversity via MaxSum algorithm
- Stopword filtering

**V2 Topics** (Enhanced):
- Noun phrase extraction (grammatical)
- MMR for diversity (λ=0.7)
- Canonicalization (merge similar)
- Timestamped evidence
- Confidence scores

**Example Topic Evolution**:
```
Raw Text: "I meditate every morning to improve my mental clarity"

V1 Output: ["meditate morning", "mental clarity", "improve"]

V2 Output: [
  {
    "tag": "morning meditation",
    "canonical": "meditation",
    "confidence": 0.82,
    "evidence": ["I meditate every morning..."]
  },
  {
    "tag": "mental clarity",
    "canonical": "mental clarity",
    "confidence": 0.75,
    "evidence": ["...improve my mental clarity"]
  }
]
```

### 4. Umbrella Clustering (Meta-Topics)

**Purpose**: Group related topics into semantic themes  
**Level**: Account-level (across all videos)  
**Algorithm**: Louvain community detection  
**Limit**: Maximum 5 umbrellas per account

**Why Umbrellas?**
- **Reduce Complexity**: 400+ topics → 5 umbrellas
- **Discover Themes**: Find hidden patterns in content
- **Improve Navigation**: Browse by high-level themes
- **Better UX**: Less overwhelming for users

**Clustering Process**:

1. **Load Topics**: Gather all canonical topics from account
   - Example: 428 unique topics from @kwrt_

2. **Generate Embeddings**: 384-dim vectors per topic
   ```python
   embeddings = model.encode(canonical_topics)
   # Shape: (428, 384)
   ```

3. **Build Similarity Graph**:
   ```python
   # Compute pairwise cosine similarity
   similarity_matrix = cosine_similarity(embeddings)
   
   # Create graph: edges where similarity ≥ threshold
   threshold = 0.7
   graph = nx.Graph()
   for i, j in combinations(range(len(topics)), 2):
       if similarity_matrix[i][j] >= threshold:
           graph.add_edge(i, j, weight=similarity_matrix[i][j])
   ```

4. **Community Detection**: Louvain algorithm finds clusters
   ```python
   communities = community_louvain.best_partition(graph)
   # Result: {0: 3, 1: 3, 2: 26, ...}  (topic_id: cluster_id)
   ```

5. **Label Generation**: Coverage-based algorithm
   ```python
   # For cluster of topics ["meditation isn", "meditate just noisy", ...]
   # Extract words: ["meditation", "meditate", "noisy", ...]
   # Score by coverage: word appears in 33 of 33 topics = 100%
   # Result: "Meditation" (single word, high coverage)
   ```

6. **Ranking & Limiting**:
   ```python
   # Sort by member_count (number of topics in cluster)
   umbrellas.sort(key=lambda u: u.member_count, reverse=True)
   
   # Keep top 5
   top_umbrellas = umbrellas[:5]
   ```

**Real Example** (@kwrt_ account):

| Umbrella | Label | Topics | Videos | Coherence |
|----------|-------|--------|--------|-----------|
| 1 | **Meditation** | 33 | 8 | 64% |
| 2 | **Identity** | 19 | 6 | 56% |
| 3 | **Spirituality** | 13 | 6 | 62% |
| 4 | **Experienced Hope** | 10 | 4 | 61% |
| 5 | **Masculinity** | 10 | 1 | 72% |

**Label Quality**:
- ✅ Broad terms (not specific phrases)
- ✅ 1-2 words maximum
- ✅ Covers majority of topics in cluster
- ✅ Proper capitalization
- ✅ UI-ready

### 5. Semantic Search

**Technology**: FAISS + SentenceTransformers  
**Index Size**: ~3MB for 150 videos  
**Query Speed**: <100ms for most queries  
**Relevance**: Cosine similarity scoring

**How It Works**:

1. **Indexing Phase** (one-time per video):
   ```python
   # Split transcript into semantic segments
   segments = split_into_sentences(transcript)
   
   # Generate embeddings
   embeddings = model.encode(segments)  # (N, 384)
   
   # Add to FAISS index
   faiss_index.add(embeddings)
   
   # Store metadata
   metadata.append({
       "text": segment,
       "video_id": video_id,
       "username": username,
       "timestamp": timestamp,
       "start_time": start,
       "end_time": end
   })
   ```

2. **Search Phase** (real-time):
   ```python
   # Embed query
   query_embedding = model.encode(query)  # (1, 384)
   
   # FAISS search (inner product)
   distances, indices = faiss_index.search(query_embedding, top_k=200)
   
   # Retrieve metadata
   results = [metadata[i] for i in indices[0]]
   
   # Score and filter
   results = [r for r in results if r['score'] >= 0.15]
   
   # Apply filters (username, category, tags, dates)
   results = apply_filters(results, filters)
   
   # Sort and return
   return sort_results(results, sort_by)
   ```

**Search Features**:

- ✅ **Semantic Matching**: Understands meaning, not just keywords
  - Query: "meditation" → Finds: "mindfulness", "awareness", "consciousness"
  
- ✅ **Multi-Creator**: Search across all creators or filter by specific ones
  
- ✅ **Advanced Filters**:
  - Usernames (include/exclude)
  - Category (Spirituality, Philosophy, etc.)
  - Tags (topic filters)
  - Date range (date_from, date_to)
  - Minimum relevance score
  
- ✅ **Snippet Generation**: 2-3 sentence context around match
  
- ✅ **Timestamp Links**: Jump to exact moment in video
  
- ✅ **Sorting Options**:
  - **Relevance**: By semantic similarity score (default)
  - **Recency**: Newest videos first
  - **Timestamp**: Chronological within video

**Example Query**:
```json
POST /api/search/semantic
{
  "query": "meditation techniques for beginners",
  "top_k": 200,
  "filters": {
    "usernames": ["kwrt_", "matrix.v5"],
    "category": "Spirituality",
    "min_score": 0.15
  },
  "sort": "relevance"
}
```

**Example Results**:
```json
{
  "query": "meditation techniques for beginners",
  "total_results": 12,
  "results": [
    {
      "text": "When you're meditating, the goal isn't to achieve some perfect state of mind...",
      "snippet": "...meditating, the goal isn't to achieve some perfect state...",
      "video_id": "7520323029956709645",
      "username": "kwrt_",
      "timestamp": "2025-10-21T07:30:15",
      "start_time": 45.2,
      "end_time": 52.8,
      "score": 0.847,
      "segment_id": 12
    }
  ]
}
```

**Performance Characteristics**:

| Corpus Size | Index Size | Search Time | Indexing Time |
|-------------|-----------|-------------|---------------|
| 50 videos | ~1 MB | 50ms | 2 min |
| 150 videos | ~3 MB | 80ms | 5 min |
| 500 videos | ~10 MB | 150ms | 15 min |
| 1000+ videos | ~20 MB | 300ms | 30 min |

### 6. Bulk Ingestion System

**Purpose**: Process multiple accounts with advanced filtering  
**Technology**: Async Python with job queue  
**UI**: Real-time progress tracking in React

**Job Queue Architecture**:

```python
class IngestionJob:
    job_id: str  # UUID
    status: IngestionStatus  # queued, running, complete, failed, paused
    accounts: List[AccountProgress]
    filters: VideoFilter
    settings: IngestionSettings
    started_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]
```

**Video Filtering Options**:

1. **Count Filters**:
   - `last_n_videos`: Process last N videos (e.g., 50)
   - `percentage`: Process top X% by view count (e.g., 20%)

2. **Date Filters**:
   - `date_from`: Only videos after date (YYYY-MM-DD)
   - `date_to`: Only videos before date

3. **History Segment**:
   - `history_start`: 0.0 (oldest) to 1.0 (newest)
   - `history_end`: Define segment of account history
   - Example: `history_start=0.5, history_end=1.0` → newest 50%

4. **Speech Filters**:
   - `only_with_speech`: Skip videos with no speech
   - `skip_no_speech`: Skip videos below threshold (default: 50 chars)

5. **Topic Filters** (planned):
   - `required_tags`: Only videos with specific topics
   - `required_category`: Only accounts in specific category

**Settings**:
- `whisper_mode`: fast, balanced, accurate, ultra
- `skip_existing`: Skip already-processed videos (idempotency)
- `retranscribe_low_confidence`: Re-transcribe if confidence < threshold
- `max_duration_minutes`: Stop after X minutes (safety)

**Progress Tracking**:

```json
{
  "job_id": "abc-123",
  "status": "transcribing",
  "accounts": [
    {
      "username": "kwrt_",
      "status": "transcribing",
      "total_videos": 50,
      "filtered_videos": 45,  // After filtering
      "processed_videos": 12,
      "skipped_videos": 0,
      "failed_videos": 0,
      "overall_progress": 26.7,  // Percentage
      "current_video": {
        "video_id": "7520122784752700686",
        "title": "taking the redpill...",
        "status": "transcribing",
        "step": "Running Whisper model...",
        "progress": 65.0,  // Percentage
        "started_at": "2025-10-23T14:32:15"
      }
    }
  ],
  "started_at": "2025-10-23T14:30:00",
  "estimated_completion": "2025-10-23T16:45:00"
}
```

**Job Control**:
- ✅ Pause job (saves state, can resume)
- ✅ Cancel job (stops immediately)
- ✅ Resume job (continues from last checkpoint)
- ✅ View all jobs (history + active)
- ✅ Job persistence (survives server restart)

**Example Usage**:
```json
POST /api/ingest/start
{
  "usernames": ["kwrt_", "matrix.v5", "beabettermandaily"],
  "filters": {
    "last_n_videos": 50,
    "only_with_speech": true,
    "date_from": "2025-01-01"
  },
  "settings": {
    "whisper_mode": "balanced",
    "skip_existing": true
  }
}
```

### 7. Authentication Support

**TikTok Cookies**: For private/age-restricted content  
**Format**: Netscape cookies.txt  
**Usage**: `--cookies cookies.txt`

**Why Needed**:
- 🔒 Private accounts
- 🔞 Age-restricted content
- 🌍 Region-locked videos
- 📺 Higher quality downloads

**How to Generate**:
1. Install browser extension (e.g., "Get cookies.txt")
2. Login to TikTok in browser
3. Export cookies.txt
4. Pass to ingestion script

**Security**:
- ⚠️ Cookies contain auth tokens
- 🔐 Keep cookies.txt private
- ♻️ Rotate cookies periodically
- 🗑️ Delete after use

---

## Topic System V1 vs V2

### Comparison Matrix

| Feature | V1 (KeyBERT) | V2 (spaCy+MMR) |
|---------|--------------|----------------|
| **Algorithm** | KeyBERT + MaxSum | spaCy NLP + MMR |
| **NLP Engine** | BERT embeddings | spaCy en_core_web_sm |
| **Diversity** | MaxSum (0.5) | MMR (λ=0.7) |
| **Quality** | Good | Excellent |
| **Canonicalization** | No | Yes (merge similar) |
| **Evidence** | No | Yes (timestamped) |
| **Confidence** | Score only | 0-1 confidence |
| **Stop Phrases** | NLTK stopwords | Custom 60+ phrases |
| **Output Size** | ~1-2 KB | ~3-5 KB |
| **Performance** | Fast (~1s/video) | Moderate (~2-3s/video) |
| **Status** | Legacy (maintained) | Production (default) |

### V1 System Details

**File**: `topic_extractor.py`  
**Lines**: ~400

**Process**:
```python
# 1. Load transcript
transcript = load_transcript(video_id)

# 2. Initialize KeyBERT
kw_model = KeyBERT()

# 3. Extract keyphrases
keywords = kw_model.extract_keywords(
    transcript,
    keyphrase_ngram_range=(1, 3),  # 1-3 words
    stop_words='english',
    use_maxsum=True,
    diversity=0.5,
    top_n=10
)

# 4. Format output
topics = [
    {
        "tag": keyword,
        "score": score,
        "type": "keyphrase"
    }
    for keyword, score in keywords
]
```

**Example Output**:
```json
{
  "video_id": "7520122784752700686",
  "title": "...",
  "tags": [
    {"tag": "attractiveness", "score": 0.4191, "type": "keyphrase"},
    {"tag": "ego attractiveness", "score": 0.4497, "type": "keyphrase"},
    {"tag": "solitude loneliness", "score": 0.5013, "type": "keyphrase"}
  ],
  "extracted_at": "2025-10-21T07:30:15"
}
```

**Strengths**:
- ✅ Fast processing
- ✅ Simple implementation
- ✅ Good baseline quality
- ✅ No external dependencies

**Weaknesses**:
- ❌ No grammatical structure (random word combinations)
- ❌ Duplicate topics (e.g., "meditation", "meditate", "meditating")
- ❌ No evidence linking
- ❌ No confidence scoring
- ❌ Limited stop phrase filtering

### V2 System Details

**File**: `topic_extractor_v2.py`  
**Lines**: 595

**Process**:
```python
# 1. Load transcript with timestamps
transcript = load_transcript(video_id)
sentences = split_sentences(transcript)
timestamps = extract_timestamps(transcript)

# 2. Extract noun phrases (spaCy)
doc = nlp(transcript)
candidates = [
    chunk.text.lower()
    for chunk in doc.noun_chunks
    if len(chunk.text) > 3
]

# 3. Filter stop phrases
candidates = [
    c for c in candidates
    if c not in stop_phrases
]

# 4. Generate embeddings
embeddings = model.encode(candidates)
doc_embedding = model.encode(transcript)

# 5. MMR selection (λ=0.7)
selected_topics = mmr_selection(
    candidates,
    embeddings,
    doc_embedding,
    lambda_param=0.7,
    top_k=10
)

# 6. Canonicalize
canonical_topics = [
    canonicalize(topic)
    for topic in selected_topics
]

# 7. Find evidence
for topic in canonical_topics:
    evidence = find_evidence(
        topic,
        sentences,
        timestamps,
        max_evidence=5
    )
    topic['evidence'] = evidence

# 8. Compute confidence
for topic in canonical_topics:
    confidence = compute_confidence(
        topic['mmr_score'],
        len(topic['evidence']),
        topic['frequency']
    )
    topic['confidence'] = confidence
```

**Example Output**:
```json
{
  "video_id": "7520122784752700686",
  "username": "kwrt_",
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
          "start": 142.5,
          "end": 148.2,
          "text": "It's believing in all this made up shit about jobs and cars and status and ego and attractiveness..."
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

**Strengths**:
- ✅ Grammatically correct phrases (noun phrases)
- ✅ Topic deduplication (canonicalization)
- ✅ Timestamped evidence (provenance)
- ✅ Confidence scoring (quality signal)
- ✅ Better diversity (MMR > MaxSum)
- ✅ Custom stop phrase filtering
- ✅ Production-ready quality

**Weaknesses**:
- ⚠️ Slower processing (2-3x V1)
- ⚠️ More complex implementation
- ⚠️ Requires spaCy model download

### Migration Path

**V1 → V2 Migration Script**: `scripts/migrate_topics_v2.py`

```bash
# Dry run (preview only)
python scripts/migrate_topics_v2.py --account kwrt_ --dry-run

# Migrate single account
python scripts/migrate_topics_v2.py --account kwrt_

# Migrate all accounts
python scripts/migrate_topics_v2.py --all

# Force re-extraction
python scripts/migrate_topics_v2.py --account kwrt_ --force
```

**Migration Statistics** (kwrt_ example):
- V1 Topics: 429 total
- V2 Topics: 428 canonical (deduplicated)
- Extraction Success: 45/50 videos (90%)
- Time: ~2 minutes for 50 videos

**Backward Compatibility**:
- V1 files preserved (`{video_id}_tags.json`)
- V2 files added (`{video_id}_tags_v2.json`)
- Both systems can coexist
- API serves V2 when available, fallback to V1

### Automatic V2 Integration

**Since**: October 2025  
**Status**: Production default

All new ingestions automatically generate V2 topics:

```python
# core/ingestion_manager.py (lines 650-710)

# V1 extraction (backward compatibility)
extract_all_topics(username)

# V2 extraction (automatic)
TopicExtractorV2().extract_account_topics_v2(username, force=False)

# Umbrella generation (automatic)
UmbrellaBuilder().build_account_umbrellas(username, max_umbrellas=5)
```

**Result**: No manual steps needed for V2 topics!

---

## Semantic Search Capabilities

### Understanding Semantic vs Keyword Search

**Keyword Search** (Traditional):
```
Query: "meditation"
Matches: Documents containing exact word "meditation"
Misses: "mindfulness", "awareness", "contemplation"
```

**Semantic Search** (TikTalk):
```
Query: "meditation"
Matches: Documents about meditation, mindfulness, awareness, contemplation
Reason: Understands meaning, not just words
```

### How Semantic Search Works

**1. Embedding Space**:
- All text converted to 384-dimensional vectors
- Similar meanings → similar vectors
- Cosine similarity measures relatedness

**Example**:
```
"meditation" → [0.12, -0.45, 0.23, ..., 0.67]  (384 dims)
"mindfulness" → [0.15, -0.42, 0.25, ..., 0.64]  (384 dims)
Cosine Similarity: 0.91 (very similar!)
```

**2. Query Processing**:
```python
# User query
query = "meditation techniques for beginners"

# Embed query
query_vector = model.encode(query)  # (384,)

# Search FAISS index
k = 200  # Retrieve top 200 candidates
distances, indices = index.search(query_vector.reshape(1, -1), k)

# distances: similarity scores (0-1, higher = more similar)
# indices: positions in index
```

**3. Filtering & Ranking**:
```python
# Retrieve metadata
results = [metadata[i] for i in indices[0]]

# Filter by minimum score
results = [r for r in results if r['score'] >= 0.15]

# Apply user filters
if filters.usernames:
    results = [r for r in results if r['username'] in filters.usernames]

if filters.category:
    # Load account categories
    results = [r for r in results if get_category(r['username']) == filters.category]

if filters.date_from or filters.date_to:
    results = filter_by_date(results, filters.date_from, filters.date_to)

# Sort by score (relevance)
results.sort(key=lambda r: r['score'], reverse=True)
```

**4. Snippet Generation**:
```python
def create_snippet(text: str, max_sentences: int = 3) -> str:
    """Generate 2-3 sentence snippet"""
    sentences = split_sentences(text)
    
    # Take first N sentences
    snippet_sentences = sentences[:max_sentences]
    
    # Join with ellipsis
    snippet = " ".join(snippet_sentences)
    
    # Truncate if too long
    if len(snippet) > 300:
        snippet = snippet[:297] + "..."
    
    return snippet
```

### Search Query Examples

**Example 1: Simple Semantic Search**
```json
POST /api/search/semantic
{
  "query": "meditation",
  "top_k": 50
}

// Finds: meditation, mindfulness, awareness, contemplation, 
// breathing exercises, inner peace, consciousness, etc.
```

**Example 2: Creator-Specific Search**
```json
{
  "query": "relationships and love",
  "filters": {
    "usernames": ["beabettermandaily", "kwrt_"]
  }
}

// Only search within these 2 creators
```

**Example 3: Category Filter**
```json
{
  "query": "personal growth strategies",
  "filters": {
    "category": "Self-Improvement"
  }
}

// Only search Self-Improvement creators
```

**Example 4: Date Range**
```json
{
  "query": "AI and technology",
  "filters": {
    "date_from": "2025-01-01",
    "date_to": "2025-03-31"
  }
}

// Only Q1 2025 content
```

**Example 5: Multi-Filter**
```json
{
  "query": "meditation techniques",
  "filters": {
    "category": "Spirituality",
    "tags": ["meditation", "mindfulness"],
    "min_score": 0.25,
    "date_from": "2025-01-01"
  },
  "sort": "relevance",
  "top_k": 100
}

// Highly specific search with multiple constraints
```

### Search Performance

**Benchmark** (150 videos, ~3MB index):

| Query Type | Results | Time | Notes |
|-----------|---------|------|-------|
| Simple query | 50 | 45ms | No filters |
| With username filter | 20 | 52ms | 1 creator |
| With category filter | 30 | 68ms | Requires category lookup |
| With date filter | 15 | 58ms | Date parsing overhead |
| Multi-filter | 10 | 75ms | All filters combined |

**Scaling**:
- FAISS is sub-linear: O(log N) with IVF index
- Current flat index: O(N) but very fast for <1M vectors
- Can handle 1M+ vectors with IVF index
- Memory efficient: 384 * 4 bytes = 1.5KB per segment

### Advanced Search Features

**1. Exact Phrase Matching** (planned):
```json
{
  "query": "meditation is not",
  "filters": {
    "exact_phrase": true
  }
}
```

**2. Boolean Queries** (planned):
```json
{
  "query": "meditation AND mindfulness NOT stress"
}
```

**3. Semantic Similarity Threshold**:
```json
{
  "query": "consciousness",
  "filters": {
    "min_score": 0.5  // Only very relevant results
  }
}
```

**4. Multi-Query Search** (planned):
```json
{
  "queries": [
    "meditation techniques",
    "breathing exercises",
    "mindfulness practices"
  ],
  "merge": "union"  // or "intersection"
}
```

---

## Ingestion Features

### Filtering Capabilities

**1. Video Count Filters**:

```python
# Last N videos
filters = {"last_n_videos": 50}

# Top percentage by views
filters = {"percentage": 0.2}  # Top 20% most viewed
```

**2. Date Range Filters**:

```python
filters = {
    "date_from": "2025-01-01",
    "date_to": "2025-12-31"
}
```

**3. History Segment Filter**:

```python
# Newest 50% of account history
filters = {
    "history_start": 0.5,  # 0.0 = oldest, 1.0 = newest
    "history_end": 1.0
}

# Middle 30-70% of history
filters = {
    "history_start": 0.3,
    "history_end": 0.7
}
```

**Use Cases**:
- Test on recent content first
- Process historical content separately
- Sample from different time periods

**4. Speech Detection Filter**:

```python
filters = {
    "only_with_speech": True,  # Skip silent videos
    "skip_no_speech": True     # Skip if transcript < 50 chars
}
```

**5. Topic/Category Filters** (planned):

```python
filters = {
    "required_tags": ["meditation", "mindfulness"],  # Videos must have these topics
    "required_category": "Spirituality"  # Account must be in this category
}
```

### Whisper Model Selection

**Performance vs Quality Tradeoff**:

```python
# Fast mode (testing, quick iteration)
settings = {"whisper_mode": "fast"}  # tiny model, 1x realtime

# Balanced mode (production default)
settings = {"whisper_mode": "balanced"}  # small model, 2x realtime

# Accurate mode (important content)
settings = {"whisper_mode": "accurate"}  # medium model, 4x realtime

# Ultra mode (critical transcription)
settings = {"whisper_mode": "ultra"}  # large model, 8x realtime
```

**Model Comparison**:

| Mode | Model | Params | Speed | Accuracy | Size | Memory |
|------|-------|--------|-------|----------|------|--------|
| fast | tiny | 39M | ~1x | 85% | 75MB | 1GB |
| balanced | small | 244M | ~2x | 92% | 483MB | 2GB |
| accurate | medium | 769M | ~4x | 96% | 1.5GB | 5GB |
| ultra | large | 1550M | ~8x | 98% | 2.9GB | 10GB |

**When to Use Each**:
- **fast**: Development, testing, iteration
- **balanced**: Production default, good quality/speed
- **accurate**: Important podcasts, lectures, interviews
- **ultra**: Legal, medical, critical content

### Idempotency Features

**Skip Existing Videos**:
```python
settings = {
    "skip_existing": True  # Default: don't reprocess
}
```

**Re-transcribe Low Confidence**:
```python
settings = {
    "retranscribe_low_confidence": True,  # Re-transcribe if confidence < threshold
    "min_confidence": 0.8
}
```

**Force Re-extraction**:
```bash
# Command-line flag
python scripts/ingest_account.py --user kwrt_ --force

# API
POST /api/ingest/start
{
  "usernames": ["kwrt_"],
  "settings": {
    "force_reprocess": true
  }
}
```

### Progress Tracking

**Multi-Level Progress**:

1. **Job Level**:
   - Overall status (queued, running, complete)
   - Total accounts, processed accounts
   - Estimated completion time

2. **Account Level**:
   - Videos found, filtered, processed, skipped, failed
   - Overall progress percentage
   - Current video being processed

3. **Video Level**:
   - Current step (downloading, transcribing, etc.)
   - Progress within step (percentage)
   - Timestamps (started_at, completed_at)

**Real-Time Updates**:
```typescript
// React component polls every 2 seconds
useEffect(() => {
  const interval = setInterval(() => {
    fetchJobStatus(jobId)
  }, 2000)
  
  return () => clearInterval(interval)
}, [jobId])
```

**Progress States**:
```python
class IngestionStatus(Enum):
    QUEUED = "queued"
    FETCHING_METADATA = "fetching_metadata"
    FILTERING = "filtering"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    EXTRACTING_TOPICS = "extracting_topics"
    EMBEDDING = "embedding"
    COMPLETE = "complete"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
```

### Batch Processing

**CSV Export**:
```bash
# Automatically generates CSV report
accounts/_batch_reports/batch_ingestion_20251021_142545.csv
```

**CSV Format**:
```csv
username,total_videos,processed,skipped,failed,duration_seconds,status
kwrt_,50,45,5,0,3600,complete
matrix.v5,30,28,2,0,2400,complete
```

**Multiple Accounts**:
```bash
# Command line
python scripts/batch_ingest.py --users kwrt_ matrix.v5 beabettermandaily

# From file
python scripts/batch_ingest.py --file accounts.txt

# accounts.txt:
kwrt_
matrix.v5
beabettermandaily
```

---

## UI/UX Features

### Visual Design

**Theme**: Cyberpunk/Neon  
**Color Palette**:
- Electric Purple (#a78bfa)
- Hot Pink (#fb7185)
- Neon Blue (#3b82f6)
- Cyber Green (#10b981)
- Dark Void (#0a0a0f)

**Design Elements**:
- 🔲 Glass-morphism panels
- ✨ Neon glow effects
- 🌊 Smooth animations
- 📊 Gradient text
- 🎨 Glassmorphic cards

**Example CSS**:
```css
.glass-panel {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.neon-glow {
  box-shadow: 0 0 20px rgba(167, 139, 250, 0.5);
  transition: all 0.3s ease;
}

.neon-glow:hover {
  box-shadow: 0 0 30px rgba(167, 139, 250, 0.8);
  transform: translateY(-2px);
}
```

### Page Features

**1. Dashboard**:
- System overview statistics
- Recent activity feed
- Quick action buttons
- Health indicators

**2. Library**:
- Grid/List view toggle
- Category badges
- Video count per creator
- Last updated timestamps
- Search/filter bar

**3. Creator Detail**:
- 3 tabs: Topics, Categories, Umbrellas
- Topic frequency display
- Category confidence scores
- V2 umbrella visualization
- Back navigation

**4. Search**:
- Large semantic search input
- Recent searches (localStorage)
- Advanced filter panel
- Result count display
- Snippet highlighting

**5. Transcripts**:
- Video cards with metadata
- Topic tags per video
- Category badges
- V2 feature banner
- Filter controls

**6. Transcript View**:
- Full transcript display
- Highlighted search terms
- Timestamp navigation
- Topic tag cloud
- Video metadata

**7. Ingest**:
- Multi-account form
- Advanced filter options
- Whisper mode selector
- Real-time progress
- Job list with controls

### Interactive Elements

**1. Search Filters**:
- Collapsible panel
- Username multi-select
- Category dropdown
- Tag multi-select
- Date range picker
- Min score slider

**2. Progress Indicators**:
- Linear progress bars
- Circular loaders
- Step indicators
- Percentage displays
- Time estimates

**3. Toasts/Notifications**:
- Success messages (green)
- Error messages (red)
- Info messages (blue)
- Warning messages (yellow)
- Auto-dismiss (5s)

**4. Empty States**:
- Graceful "no results" messages
- Contextual suggestions
- Call-to-action buttons
- Helpful illustrations

**5. Loading States**:
- Skeleton loaders
- Spinner animations
- Progressive loading
- Lazy loading (images)

### Responsive Design

**Breakpoints**:
```css
/* Mobile */
@media (max-width: 640px) { }

/* Tablet */
@media (min-width: 641px) and (max-width: 1024px) { }

/* Desktop */
@media (min-width: 1025px) { }
```

**Responsive Features**:
- ✅ Mobile-first design
- ✅ Touch-friendly buttons (44px min)
- ✅ Responsive typography
- ✅ Collapsible sidebars
- ✅ Stack → Grid transitions
- ✅ Hamburger menus (mobile)

### Accessibility

**Features** (via Radix UI):
- ✅ Keyboard navigation
- ✅ Focus indicators
- ✅ ARIA labels
- ✅ Screen reader support
- ✅ Color contrast (WCAG AA)
- ✅ Skip links
- ✅ Semantic HTML

---

## Data Quality Features

### 1. Canonicalization

**Purpose**: Merge similar topics to reduce redundancy

**Rules** (`config/canonical_topics.json`):
```json
{
  "merge_rules": {
    "meditate": "meditation",
    "meditating": "meditation",
    "meditations": "meditation",
    
    "lucid dream": "lucid dreaming",
    "lucid dreams": "lucid dreaming",
    
    "AI": "artificial intelligence",
    "machine learning": "machine learning",
    "ML": "machine learning"
  },
  "auto_merge_threshold": {
    "cosine_similarity": 0.9,
    "edit_distance_max": 2
  }
}
```

**Automatic Merging**:
```python
def canonicalize(topic: str) -> str:
    # 1. Check explicit rules
    if topic in merge_rules:
        return merge_rules[topic]
    
    # 2. Find similar existing canonicals
    topic_embedding = model.encode(topic)
    
    for canonical, embedding in canonical_embeddings.items():
        similarity = cosine_similarity(topic_embedding, embedding)
        
        if similarity >= 0.9:  # Very similar
            return canonical
    
    # 3. Check edit distance
    for canonical in canonicals:
        if edit_distance(topic, canonical) <= 2:  # Close spelling
            return canonical
    
    # 4. Return as-is (new canonical)
    return topic
```

**Benefits**:
- ✅ Reduces duplicate topics
- ✅ Improves aggregation accuracy
- ✅ Better umbrella clustering
- ✅ Cleaner UI display

### 2. Stop Phrase Filtering

**Purpose**: Remove generic, uninformative phrases

**Stop Phrases** (`config/stop_phrases.txt`):
```
# Generic video phrases
thank watching video
thank watching
watching video
video
video video

# Meta phrases
link bio
description
comment
subscribe

# Filler phrases
going talk
want talk
today going
```

**Filtering**:
```python
# Load stop phrases
stop_phrases = set(load_stop_phrases())

# Filter candidates
filtered_topics = [
    topic for topic in candidates
    if topic.lower() not in stop_phrases
]
```

**Benefits**:
- ✅ Cleaner topic lists
- ✅ More meaningful topics
- ✅ Better search results
- ✅ Reduced noise

### 3. Confidence Scoring

**V2 Confidence Formula**:
```python
def compute_confidence(mmr_score: float, 
                       evidence_count: int, 
                       frequency: int) -> float:
    # Normalize MMR score [-0.5, 0.7] → [0, 1]
    normalized_mmr = (mmr_score + 0.5) / 1.2
    
    # Evidence boost (up to +0.3)
    evidence_boost = min(0.3, np.log1p(evidence_count) / 10)
    
    # Frequency boost (planned)
    # frequency_boost = min(0.1, np.log1p(frequency) / 20)
    
    # Final confidence
    confidence = min(1.0, normalized_mmr + evidence_boost)
    
    return confidence
```

**Confidence Levels**:
- **0.0-0.3**: Low (questionable relevance)
- **0.3-0.5**: Medium (possibly relevant)
- **0.5-0.7**: Good (likely relevant)
- **0.7-0.9**: High (very relevant)
- **0.9-1.0**: Excellent (definitely relevant)

**Usage**:
- Filter low-confidence topics (< 0.3)
- Prioritize high-confidence in UI
- Re-extract if confidence too low

### 4. Evidence Linking

**Purpose**: Provide provenance for topics

**Evidence Structure**:
```json
{
  "evidence": [
    {
      "sentence_index": 30,
      "start": 142.5,
      "end": 148.2,
      "text": "It's believing in all this made up shit about jobs and cars and status and ego and attractiveness..."
    },
    {
      "sentence_index": 35,
      "start": 152.0,
      "end": 157.5,
      "text": "Being attractive does come with a lot of benefits but..."
    }
  ]
}
```

**Benefits**:
- ✅ Transparency: See why topic was extracted
- ✅ Verification: Manually check accuracy
- ✅ Context: Understand topic usage
- ✅ Timestamps: Jump to relevant moment

### 5. Diversity Control

**MaxSum (V1)**:
```python
# Balance similarity vs diversity
diversity = 0.5  # 0=similar, 1=diverse

keywords = kw_model.extract_keywords(
    text,
    use_maxsum=True,
    diversity=diversity
)
```

**MMR (V2)**:
```python
# λ controls relevance vs diversity
lambda_param = 0.7  # 70% relevance, 30% diversity

def mmr_selection(candidates, embeddings, doc_embedding, lambda_param, top_k):
    selected = []
    selected_embeddings = []
    
    while len(selected) < top_k:
        # Relevance to document
        relevance_scores = cosine_similarity(embeddings, doc_embedding)
        
        # Redundancy with selected
        if len(selected) > 0:
            redundancy_scores = cosine_similarity(embeddings, selected_embeddings).max(axis=1)
        else:
            redundancy_scores = np.zeros(len(candidates))
        
        # MMR score
        mmr_scores = lambda_param * relevance_scores - (1 - lambda_param) * redundancy_scores
        
        # Select best
        best_idx = mmr_scores.argmax()
        selected.append(candidates[best_idx])
        selected_embeddings.append(embeddings[best_idx])
        
        # Remove from candidates
        candidates = np.delete(candidates, best_idx)
        embeddings = np.delete(embeddings, best_idx, axis=0)
    
    return selected
```

**Result**:
- ✅ Diverse topics (not redundant)
- ✅ Relevant topics (not random)
- ✅ Balanced representation
- ✅ Better coverage

### 6. Quality Metrics

**Per-Topic Metrics**:
- **Confidence**: 0-1 quality score
- **MMR Score**: Relevance - redundancy
- **Evidence Count**: Number of supporting sentences
- **Frequency**: Occurrences across videos

**Per-Account Metrics**:
- **Total Topics**: Unique topics extracted
- **Canonical Topics**: After deduplication
- **Average Confidence**: Mean confidence across all topics
- **Coherence**: Avg similarity within umbrella clusters

**System Metrics**:
- **Extraction Success Rate**: % videos successfully processed
- **Transcription Confidence**: Whisper confidence scores
- **Index Coverage**: % transcripts in search index

---

## Advanced Capabilities

### 1. Custom Embeddings (Future)

**Current**: all-MiniLM-L6-v2 (384 dims, general-purpose)

**Planned**:
- Domain-specific fine-tuning
- Multi-lingual support (100+ languages)
- Larger models (768, 1024 dims)
- Custom training on TikTok corpus

### 2. Real-Time Ingestion (Future)

**Current**: Batch ingestion via API/CLI

**Planned**:
- WebSocket connection for live progress
- Server-Sent Events (SSE)
- Automatic account monitoring
- Webhook notifications

### 3. Recommendation Engine (Future)

**Capabilities**:
- "Videos like this" based on topics
- "Creators similar to..." based on embeddings
- "Users who liked this also liked..."
- Personalized content discovery

**Algorithm**:
```python
def recommend_similar_videos(video_id: str, top_k: int = 10):
    # Get video topics
    topics = get_video_topics(video_id)
    
    # Get topic embeddings
    topic_embeddings = model.encode(topics)
    
    # Find videos with similar topics
    similar_videos = search_by_embedding(topic_embeddings, top_k)
    
    return similar_videos
```

### 4. Trend Analysis (Future)

**Capabilities**:
- Track topic popularity over time
- Identify emerging topics
- Creator topic evolution
- Cross-creator trend comparison

**Visualization**:
- Time series charts
- Topic heatmaps
- Network graphs
- Trend curves

### 5. Multi-Modal Search (Future)

**Beyond Text**:
- Video thumbnail search
- Audio fingerprinting
- Scene detection
- Emotion recognition

### 6. Export & Integration

**Current**:
- CSV batch reports
- JSON API responses

**Planned**:
- Excel export
- PDF reports
- Zapier integration
- Webhook notifications
- GraphQL API

---

## Limitations & Constraints

### Technical Limitations

**1. Language Support**:
- Currently: English-optimized
- Whisper: 99 languages, but quality varies
- spaCy: English model only (planned: multi-lingual)
- Embeddings: English-biased

**2. Video Length**:
- Optimal: 1-10 minutes
- Maximum: No hard limit, but >1 hour slows significantly
- Whisper: Can process any length, but memory constraints

**3. Corpus Size**:
- Current: Tested up to 500 videos
- FAISS: Can scale to millions (with IVF index)
- Storage: ~3-5KB per video (topics), ~10-50KB (embeddings)

**4. Real-Time Constraints**:
- Transcription: Not real-time (slower than video length)
- Search: Real-time (<100ms)
- Topic extraction: ~2-3s per video
- Umbrella clustering: ~5-10s per account

### Business Limitations

**1. TikTok API**:
- No official API access
- Relies on yt-dlp (scraping)
- Rate limiting possible
- Cookie authentication required for some content

**2. Whisper Licensing**:
- Open source (MIT license)
- No commercial restrictions
- Models freely available

**3. Content Restrictions**:
- Age-restricted: Requires authentication
- Private accounts: Requires authentication
- Deleted videos: Cannot retrieve
- Region-locked: May need VPN

### Accuracy Limitations

**1. Transcription Errors**:
- Whisper accuracy: 85-98% (model-dependent)
- Accents: May reduce accuracy
- Background noise: Can cause errors
- Multiple speakers: May confuse attribution

**2. Topic Extraction**:
- Semantic understanding: Good but not perfect
- Domain-specific terms: May miss niche vocabulary
- Sarcasm/irony: Not detected
- Context: Limited to single video

**3. Category Classification**:
- Fixed 15 categories: May not fit all content
- Confidence: Can be ambiguous for multi-topic creators
- Bias: Categories reflect training data

### Scalability Constraints

**Current System**:
- Designed for: 10-50 accounts, 1000+ videos
- Tested at: 14 accounts, 150 videos
- Works well at this scale

**Scaling Challenges**:

| Component | Current Limit | Scaling Solution |
|-----------|---------------|------------------|
| Transcription | CPU-bound | GPU acceleration |
| FAISS Index | 1M vectors (flat) | IVF clustering |
| Topic Extraction | Single-threaded | Multiprocessing |
| Storage | Local disk | Cloud storage (S3) |
| API Server | Single process | Load balancing |
| Database | JSON files | PostgreSQL/MongoDB |

**Future Scaling**:
- **10K videos**: Current architecture works
- **100K videos**: Need FAISS IVF, multiprocessing
- **1M+ videos**: Need distributed system, cloud infrastructure

---

*Document 2 of 3 - Continue to TECHNICAL_SPECIFICATIONS.md*
