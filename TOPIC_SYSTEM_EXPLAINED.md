# Topic System Architecture

## Overview

The TikTok Learning Platform uses **semantic AI** to automatically understand and tag content. This document explains how the topic extraction, aggregation, and categorization system works.

---

## 1. Topic Extraction (Per Video)

### Technology Stack

- **KeyBERT** - Extracts meaningful keyphrases using BERT embeddings
- **SentenceTransformers** (`all-MiniLM-L6-v2`) - Creates semantic embeddings
- **MaxSum Algorithm** - Ensures diverse, non-redundant topics
- **NLTK** - Natural language processing and stopword filtering

### Process Flow

1. **Input**: Full transcript text from video
2. **Keyphrase Extraction**: KeyBERT extracts 1-3 word phrases
3. **Semantic Scoring**: Each phrase scored by relevance (0-1 scale)
4. **Filtering**: Removes stopwords and generic terms
5. **Output**: Top 3-10 most meaningful topics

### Configuration

```python
keyphrase_ngram_range=(1, 3)  # Extract 1-3 word phrases
stop_words='english'           # Filter English stopwords
use_maxsum=True                # Enable diversity
nr_candidates=20               # Consider top 20 candidates
top_n=10                       # Return max 10 topics
diversity=0.5                  # Balance similarity vs diversity
```

### Real Example

**Video**: `7520122784752700686` by @kwrt_  
**Title**: "taking the redpill #redpilltiktok #men #looksmax #masculinity #matrix"

**Extracted Topics**:
```json
[
  {
    "tag": "attractiveness",
    "score": 0.4191,
    "type": "keyphrase"
  },
  {
    "tag": "looks personality problems",
    "score": 0.4199,
    "type": "keyphrase"
  },
  {
    "tag": "ego attractiveness",
    "score": 0.4497,
    "type": "keyphrase"
  },
  {
    "tag": "barely like loneliness",
    "score": 0.4577,
    "type": "keyphrase"
  },
  {
    "tag": "status ego attractiveness",
    "score": 0.4621,
    "type": "keyphrase"
  },
  {
    "tag": "like loneliness solitude",
    "score": 0.4654,
    "type": "keyphrase"
  },
  {
    "tag": "solitude loneliness",
    "score": 0.5013,
    "type": "keyphrase"
  }
]
```

---

## 2. Account-Level Topic Aggregation

### Process

After all videos are processed for a creator:

1. **Collect**: Gather all topics from all videos
2. **Count**: Track frequency (how many videos mention each topic)
3. **Score**: Calculate average score across occurrences
4. **Rank**: Sort by combined_score (frequency × avg_score × engagement_weight)
5. **Store**: Save to `account_tags.json`

### Data Structure

```json
{
  "total_tags": 429,
  "total_videos": 45,
  "tags": [
    {
      "tag": "thank watching video",
      "frequency": 2,
      "avg_score": 0.5699,
      "engagement_weight": 1.0,
      "combined_score": 1.1398,
      "video_ids": ["7552739292049607949", "7531842643249089847"]
    }
  ]
}
```

### Real Example - @kwrt_

**Stats**: 429 total tags extracted from 45 videos

**Top Topics**:
1. `thank watching video` - appears in 2 videos
2. `lack self` - appears in 2 videos
3. `meditation isn` - appears in 2 videos
4. `video` - appears in 3 videos
5. `thank watching` - appears in 2 videos
6. `self` - appears in 2 videos
7. `watching video` - appears in 2 videos
8. `understanding enlightenment` - appears in 1 video
9. `meditate just noisy` - appears in 1 video
10. `things apparent meditate` - appears in 1 video

---

## 3. Category Classification

### Predefined Categories

The system classifies creators into 15 broad categories:

- **Philosophy** - Abstract thinking, existential questions
- **Spirituality** - Meditation, consciousness, awakening
- **Self-Improvement** - Personal growth, habits, productivity
- **Psychology** - Human behavior, mental models
- **Business** - Entrepreneurship, strategy, leadership
- **Health** - Fitness, nutrition, wellness
- **Tech** - Technology, programming, innovation
- **Politics** - Government, policy, social issues
- **History** - Historical events, context, analysis
- **Creativity** - Art, design, creative process
- **Education** - Teaching, learning, knowledge
- **Entertainment** - Comedy, storytelling, pop culture
- **Music** - Musical theory, performance, composition
- **Art** - Visual arts, aesthetics, craft
- **Science** - Research, experiments, discoveries

### Classification Process

1. **Aggregate**: Combine all transcript text for creator
2. **Embed**: Generate semantic embedding representation
3. **Compare**: Calculate cosine similarity against all 15 category embeddings
4. **Score**: Produce confidence score (0-1) for each category
5. **Assign**: Select highest-scoring category as primary

### Real Example - @kwrt_

```json
{
  "category": "Spirituality",
  "confidence": 0.531,
  "all_scores": {
    "Spirituality": 0.531,      ← Winner (53.1%)
    "Philosophy": 0.464,
    "Psychology": 0.453,
    "Science": 0.440,
    "Self-Improvement": 0.443,
    "Health": 0.431,
    "Entertainment": 0.435,
    "Music": 0.431,
    "Art": 0.420,
    "Education": 0.407,
    "Creativity": 0.394,
    "Politics": 0.348,
    "History": 0.332,
    "Business": 0.331,
    "Tech": 0.283
  }
}
```

---

## 4. Topic Patterns by Category

### Spirituality Creators

**@kwrt_**:
- meditation isn
- lack self
- understanding enlightenment
- meditate just noisy
- things apparent meditate
- self
- ego attractiveness
- solitude loneliness

**@matrix.v5**:
- life lucid dreams
- available consciousness dreamscape
- dreaming approach discernment
- dreamscape believe feel
- gilded cage spiritual
- warning issued dreaming
- dreams chaotic
- dream instability

### Health Creators

**@beabettermandaily**:
- women ghosted
- pain knowledge wrong
- kindness attracted suitors
- help avoid pain
- definition pain
- learn pain deeply
- trust kindness attracted
- remember pain construct

---

## 5. How Topics Are Used in the Platform

### Search & Discovery

**Semantic Search**:
- Search "meditation" → finds videos about "mindfulness", "awareness", "consciousness"
- Search "relationships" → finds "ego attractiveness", "women ghosted", "kindness attracted"
- Embedding-based matching (not just keyword matching)

**Filter Options**:
- Filter by creator category (Spirituality, Health, Philosophy)
- Filter by specific topic tags
- Combine filters for precise discovery

### Creator Profiles

**Topics Tab**:
- Displays all extracted topics ranked by frequency
- Shows which videos contain each topic
- Helps understand creator's content themes

**Categories Tab**:
- Shows confidence scores for all 15 categories
- Visualizes content distribution
- Identifies cross-category creators

### Transcripts Page

**Metadata Display**:
- Shows top 5 tags per transcript
- Category badge for quick identification
- Enables filtering by tags and categories

---

## 6. Quality Features

### Diversity Control

**Problem**: Without diversity, similar topics dominate
```
Bad: ["meditation", "meditate", "meditating", "meditations"]
```

**Solution**: MaxSum algorithm with `diversity=0.5`
```
Good: ["meditation", "consciousness", "awareness", "mindfulness"]
```

### Score Thresholding

Only high-quality, semantically relevant topics are extracted:
- Minimum score threshold filters noise
- Average scores aggregated across videos
- Combined scores weight frequency and relevance

### N-gram Range

Supports single words through three-word phrases:

**Unigrams** (1 word):
- `meditation`
- `self`
- `attractiveness`

**Bigrams** (2 words):
- `lack self`
- `watching video`
- `solitude loneliness`

**Trigrams** (3 words):
- `understanding enlightenment`
- `ego attractiveness`
- `life lucid dreams`

### Stopword Filtering

Removes common words that add no semantic value:
- Articles: `the`, `a`, `an`
- Pronouns: `I`, `you`, `he`, `she`, `they`
- Prepositions: `in`, `on`, `at`, `from`, `to`
- Conjunctions: `and`, `but`, `or`, `because`

---

## 7. Technical Implementation

### Files Generated Per Account

```
accounts/{username}/
├── index.json                           # Video metadata
├── transcriptions/                      # Raw transcript text
│   └── {video_id}_transcript.txt
└── topics/                              # Topic extraction results
    ├── account_tags.json                # Aggregated account topics
    ├── account_category.json            # Category classification
    └── {video_id}_tags.json             # Per-video topics
```

### Topic Extraction Script

**Location**: `topic_extractor.py`

**Key Classes**:
- `TopicExtractor` - Main extraction engine
- Uses KeyBERT for keyphrase extraction
- Uses SentenceTransformers for embeddings
- Implements MaxSum for diversity

**Usage**:
```bash
# Extract topics for specific account
python topic_extractor.py extract @username

# Extract topics for all accounts
python topic_extractor.py extract-all

# Re-extract with different settings
python topic_extractor.py extract @username --max-tags 15 --diversity 0.7
```

### API Endpoints

**Get Account Topics**:
```
GET /api/accounts/{username}/tags
```

**Response**:
```json
{
  "total_tags": 429,
  "total_videos": 45,
  "tags": [...]
}
```

**Get Account Category**:
```
GET /api/accounts/{username}/category
```

**Response**:
```json
{
  "category": "Spirituality",
  "confidence": 0.531,
  "all_scores": {...}
}
```

**Get Video Topics**:
```
GET /api/accounts/{username}/tags/video/{video_id}
```

**Response**:
```json
{
  "video_id": "7520122784752700686",
  "title": "...",
  "tags": [...]
}
```

---

## 8. Benefits & Use Cases

### ✅ Automatic Content Understanding

- No manual tagging required
- Consistent across all creators
- Scales to hundreds of videos

### ✅ Semantic Intelligence

- Understands meaning, not just keywords
- "meditation" matches "mindfulness", "awareness", "consciousness"
- Context-aware topic extraction

### ✅ Discoverability

- Search by semantic meaning
- Filter by category and tags
- Browse related content

### ✅ Content Insights

- Understand creator themes
- Identify content patterns
- Compare creators by category

### ✅ User Experience

- Relevant search results
- Accurate filters
- Meaningful content organization

---

## 9. Future Enhancements

### Potential Improvements

1. **Topic Clustering**: Group similar topics into broader themes
2. **Trend Analysis**: Track topic popularity over time
3. **Recommendation Engine**: Suggest videos based on topic similarity
4. **Multi-language Support**: Extend to non-English content
5. **Custom Categories**: Allow users to define custom categories
6. **Topic Evolution**: Track how creator topics change over time

### Advanced Features

- **Topic Networks**: Visualize relationships between topics
- **Cross-Creator Analysis**: Find creators with similar topics
- **Topic-based Playlists**: Auto-generate playlists by theme
- **Semantic Deduplication**: Identify duplicate/similar content

---

## 10. Real-World Examples

### Example 1: Philosophy Video

**Transcript Excerpt**:
> "Looks maxing fucking sucks... Being attractive does come with a lot of benefits... But since when was the only fucking point of life external validation?... Loneliness is a lack of love... These are things you can give to yourself..."

**Extracted Topics**:
- `attractiveness` (0.42)
- `ego attractiveness` (0.45)
- `solitude loneliness` (0.50)
- `looks personality problems` (0.42)
- `status ego attractiveness` (0.46)

**Category**: Spirituality (53.1%)

### Example 2: Lucid Dreaming Video

**Extracted Topics**:
- `life lucid dreams` (0.58)
- `consciousness dreamscape` (0.56)
- `dreaming approach discernment` (0.54)
- `available consciousness dreamscape` (0.52)
- `gilded cage spiritual` (0.48)

**Category**: Spirituality (61.2%)

### Example 3: Relationship Advice Video

**Extracted Topics**:
- `women ghosted` (0.62)
- `kindness attracted suitors` (0.58)
- `pain knowledge wrong` (0.55)
- `help avoid pain` (0.53)
- `definition pain` (0.51)

**Category**: Health (67.8%)

---

## Conclusion

The topic system gives your TikTok library a "brain" that understands what each video is actually about. By combining:

- **KeyBERT** for intelligent keyphrase extraction
- **Sentence Transformers** for semantic understanding
- **MaxSum** for diversity and quality
- **Category embeddings** for classification

The platform can automatically organize, search, and surface content in meaningful ways—without any manual intervention.

**Key Takeaway**: Semantic AI transforms raw transcripts into structured, searchable, discoverable knowledge.

---

*Last Updated: October 23, 2025*
