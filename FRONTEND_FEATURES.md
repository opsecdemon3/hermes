# Frontend UI Features Documentation

## Overview
Complete documentation of all UI features, user interactions, and backend API integrations for the Synapse TikTok Learning Platform.

---

## Navigation & Layout

### Sidebar (Desktop)
**Location**: `src/components/Sidebar.tsx`

**Features**:
- Fixed left sidebar with navigation links
- 5 main navigation items:
  1. **Library** → `/library`
  2. **Search** → `/search`
  3. **Transcripts** → `/transcripts`
  4. **Dashboard** → `/dashboard`
  5. **Ingest** → `/ingest`

**Backend Integration**: None (pure navigation)

---

### Mobile Navigation
**Location**: `src/components/Sidebar.tsx` (MobileNav component)

**Features**:
- Bottom navigation bar for mobile devices
- Same 5 navigation items as desktop
- Icons with labels

**Backend Integration**: None (pure navigation)

---

## Page 1: Search Page
**Route**: `/search`  
**File**: `src/pages/SearchPage.tsx`

### Features & Interactions

#### 1. Search Input
- **Type**: Text input with submit button
- **User Action**: Enter search query and press "Search" button or hit Enter
- **Backend API**: `POST /api/search/semantic`
- **Payload**:
  ```json
  {
    "query": "user search text",
    "top_k": 200,
    "filters": { /* filter object */ },
    "sort": "relevance"
  }
  ```
- **Response**: Array of `SearchResult` objects
- **Use Case**: Semantic search across all transcript content to find ideas/concepts

#### 2. Recent Searches
- **Type**: Clickable pills/badges
- **User Action**: Click a recent search term to re-run that search
- **Storage**: Local storage via `useKV` hook
- **Backend API**: Same as Search Input
- **Use Case**: Quick access to previously searched topics

#### 3. Search Filters (Toggle)
- **Type**: Collapsible filter panel
- **User Action**: Click filter button to show/hide advanced filters
- **Component**: `SearchFilters` component
- **Backend API**: None (toggles UI only)

#### 4. Search Filters - Creator Filter
- **Type**: Multi-select creator list
- **User Action**: Click creator names to include/exclude from search
- **Backend API**: `GET /api/search/filter-options` (loads available creators)
- **Filter Effect**: Adds `filters.usernames` or `filters.exclude_usernames` to search request
- **Use Case**: Narrow search to specific creators or exclude certain creators

#### 5. Search Filters - Tag Filter
- **Type**: Multi-select tag buttons
- **User Action**: Click tags to filter by topic
- **Backend API**: `GET /api/search/filter-options` (loads available tags)
- **Filter Effect**: Adds `filters.tags` array to search request
- **Use Case**: Find content tagged with specific topics

#### 6. Search Filters - Category Filter
- **Type**: Single-select dropdown
- **User Action**: Select a category (Health, Technology, etc.)
- **Backend API**: `GET /api/search/filter-options` (loads available categories)
- **Filter Effect**: Adds `filters.category` to search request
- **Use Case**: Filter by broad content category

#### 7. Search Filters - Minimum Score Slider
- **Type**: Range slider
- **User Action**: Drag slider to set minimum relevance score (0.0 - 1.0)
- **Default**: 0.15
- **Filter Effect**: Adds `filters.min_score` to search request
- **Use Case**: Filter out low-relevance results

#### 8. Clear Filters Button
- **Type**: Button
- **User Action**: Click to reset all filters
- **Effect**: Removes all filter parameters and re-runs search
- **Use Case**: Start fresh search without filters

#### 9. Search Result Cards
- **Type**: Clickable cards showing transcript snippets
- **User Action**: Click "Open At Timestamp" button
- **Navigation**: `/transcript/{username}/{videoId}?query={searchQuery}`
- **Backend API**: None (navigation only)
- **Use Case**: View full transcript with highlighted segments

---

## Page 2: Library Page
**Route**: `/library`  
**File**: `src/pages/LibraryPage.tsx`

### Features & Interactions

#### 1. Creator Search Input
- **Type**: Text input with search icon
- **User Action**: Type to filter creators
- **Filter**: Client-side filtering by username or category
- **Backend API**: None (filters local data)
- **Use Case**: Find specific creators in library

#### 2. Load Creators
- **Type**: Auto-load on page mount
- **Backend API**: `GET /api/accounts`
- **Response**: Array of `Creator` objects with:
  - `username`
  - `category`
  - `video_count`
  - `last_updated`
  - `top_topics` (array)
  - `has_transcripts`, `has_tags`, `has_category` (booleans)
- **Use Case**: Display all ingested TikTok creators

#### 3. Creator Cards
- **Type**: Clickable cards
- **User Action**: Click card to view creator details
- **Navigation**: `/creator/{username}`
- **Backend API**: None (navigation only)
- **Use Case**: Browse creator library and access individual creator pages

---

## Page 3: Creator Detail Page
**Route**: `/creator/{username}`  
**File**: `src/pages/CreatorDetailPage.tsx`

### Features & Interactions

#### 1. Back Button
- **Type**: Navigation button
- **User Action**: Click to return to library
- **Navigation**: `/library`
- **Backend API**: None

#### 2. Load Creator Tags
- **Type**: Auto-load on page mount
- **Backend API**: `GET /api/accounts/{username}/tags`
- **Response**: Array of `CategoryTag` objects with:
  - `tag` (string)
  - `count` (number)
- **Use Case**: Display topic distribution for creator

#### 3. Load Creator Categories
- **Type**: Auto-load on page mount
- **Backend API**: `GET /api/accounts/{username}/category`
- **Response**: Array of `CategoryTag` objects with:
  - `tag` (category name)
  - `count` (video count)
  - `percentage` (percentage of videos)
- **Use Case**: Display content category breakdown

#### 4. Topics Tab
- **Type**: Tab panel with tag badges
- **Display**: All topics with occurrence counts
- **Backend API**: None (displays loaded data)
- **Use Case**: See what topics this creator covers

#### 5. Categories Tab
- **Type**: Tab panel with category cards
- **Display**: Content categories with percentages
- **Backend API**: None (displays loaded data)
- **Use Case**: Understand creator's content distribution

---

## Page 4: Transcript Page
**Route**: `/transcript/{username}/{videoId}`  
**File**: `src/pages/TranscriptPage.tsx`

### Features & Interactions

#### 1. Back Button
- **Type**: Navigation button
- **User Action**: Click to go back to previous page
- **Navigation**: `navigate(-1)` (browser history)
- **Backend API**: None

#### 2. Watch Video Button
- **Type**: Button
- **User Action**: Click to watch video (placeholder)
- **Current**: No backend integration
- **Future**: Could open TikTok video link
- **Use Case**: Navigate to original video

#### 3. Load Transcript
- **Type**: Auto-load on page mount
- **Backend API**: `GET /api/transcript/{username}/{videoId}?query={query}`
- **Query Parameters**:
  - `query` (optional): Search query to highlight
  - `highlights` (optional): Specific text to highlight
- **Response**: `Transcript` object with:
  - `segments` (array of transcript segments)
  - `highlighted_count` (number of highlighted segments)
- **Use Case**: View full video transcript with search highlights

#### 4. Transcript Viewer
- **Type**: Component displaying timestamped segments
- **Component**: `TranscriptViewer`
- **Features**:
  - Displays segments with timestamps
  - Highlights matching segments based on query
  - Click timestamps (handler placeholder)
- **Backend API**: None (displays loaded data)
- **Use Case**: Read and navigate transcript content

#### 5. Timestamp Clicks
- **Type**: Clickable timestamp links
- **User Action**: Click timestamp
- **Current**: Handler exists but not implemented
- **Future**: Could jump to specific time in video
- **Use Case**: Navigate to specific moment in video

---

## Page 5: Dashboard Page
**Route**: `/dashboard`  
**File**: `src/pages/DashboardPage.tsx`

### Features & Interactions

#### 1. Load System Status
- **Type**: Auto-load on page mount
- **Backend API**: `GET /api/verify/system`
- **Response**: `SystemStatus` object with:
  - `status` ("healthy" | "degraded" | "error")
  - `total_creators` (number)
  - `total_transcripts` (number)
  - `total_vectors` (number - indexed embeddings)
  - `timestamp` (last verification time)
- **Use Case**: Monitor system health and data metrics

#### 2. Re-verify System Button
- **Type**: Action button
- **User Action**: Click to trigger system re-verification
- **Backend API**: `POST /api/verify/system`
- **Response**: Updated `SystemStatus` object
- **Use Case**: Force refresh of system metrics

#### 3. System Metrics Display
- **Type**: Stat cards
- **Display**:
  - Total Creators
  - Total Transcripts
  - Indexed Vectors
  - System Status
  - Average vectors per transcript (calculated)
  - Last verified timestamp
- **Backend API**: None (displays loaded data)
- **Use Case**: View system statistics at a glance

---

## Page 6: Ingestion Manager
**Route**: `/ingest`  
**File**: `src/pages/IngestPage.tsx`

### Features & Interactions

#### 1. Input Mode Toggle
- **Type**: Button group (Single / Bulk)
- **User Action**: Switch between single username or bulk input
- **Modes**:
  - **Single**: One text input for single username
  - **Bulk**: Textarea for multiple usernames (newline or comma-separated)
- **Backend API**: None (UI state only)
- **Use Case**: Choose ingestion input method

#### 2. Upload .txt File
- **Type**: File upload button
- **User Action**: Click to select .txt file with usernames
- **Processing**: Reads file content into bulk textarea
- **Backend API**: None (client-side file reading)
- **Use Case**: Bulk upload username lists

#### 3. Username Input (Single Mode)
- **Type**: Text input
- **Placeholder**: "Enter TikTok username (e.g., @creator or creator)"
- **Backend API**: None (input only)
- **Use Case**: Enter single username for ingestion

#### 4. Username Input (Bulk Mode)
- **Type**: Textarea
- **Format**: One username per line or comma-separated
- **Live Counter**: Shows detected username count
- **Backend API**: None (input only)
- **Use Case**: Enter multiple usernames for batch ingestion

#### 5. Video Filters - Count Limit
- **Type**: Button group (5, 10, 25, 50, 100)
- **User Action**: Click to set max videos to ingest
- **Filter**: `filters.last_n_videos`
- **Backend Integration**: Passed to `/api/ingest/start`
- **Use Case**: Limit number of videos to process per creator

#### 6. Video Filters - History Segment
- **Type**: Dual range sliders
- **Range**: 0% (oldest) to 100% (newest)
- **User Action**: Drag sliders to select portion of creator's history
- **Filters**: `filters.history_start` and `filters.history_end`
- **Backend Integration**: Passed to `/api/ingest/start`
- **Use Case**: Ingest specific time period of creator's content

#### 7. Video Filters - Category Filter
- **Type**: Dropdown select
- **User Action**: Select required account category
- **Backend API**: `GET /api/search/filter-options` (loads categories)
- **Filter**: `filters.required_category`
- **Backend Integration**: Passed to `/api/ingest/start`
- **Use Case**: Only ingest accounts matching category

#### 8. Video Filters - Topic Tags
- **Type**: Multi-select tag buttons
- **User Action**: Click tags to require specific topics
- **Backend API**: `GET /api/search/filter-options` (loads tags)
- **Filter**: `filters.required_tags` (array)
- **Backend Integration**: Passed to `/api/ingest/start`
- **Use Case**: Only ingest videos with specific topics

#### 9. Video Filters - Speech Detection
- **Type**: Two checkboxes
- **Options**:
  - "Skip videos with no speech"
  - "Only videos with speech"
- **Filters**: `filters.skip_no_speech` and `filters.only_with_speech`
- **Backend Integration**: Passed to `/api/ingest/start`
- **Use Case**: Filter by speech content

#### 10. Ingestion Settings - Whisper Mode
- **Type**: Button group (Fast / Balanced / Accurate / Ultra)
- **User Action**: Select transcription quality/speed tradeoff
- **Setting**: `settings.whisper_mode`
- **Backend Mapping**: 
  - fast → tiny model
  - balanced → small model
  - accurate → medium model
  - ultra → large-v3 model
- **Backend Integration**: Passed to `/api/ingest/start`
- **Use Case**: Choose transcription accuracy vs speed

#### 11. Ingestion Settings - Skip Existing
- **Type**: Checkbox
- **User Action**: Toggle whether to skip already transcribed videos
- **Setting**: `settings.skip_existing`
- **Default**: true
- **Backend Integration**: Passed to `/api/ingest/start`
- **Use Case**: Avoid re-processing existing transcripts

#### 12. Ingestion Settings - Retranscribe Low Confidence
- **Type**: Checkbox
- **User Action**: Toggle whether to re-process low confidence transcripts
- **Setting**: `settings.retranscribe_low_confidence`
- **Default**: false
- **Backend Integration**: Passed to `/api/ingest/start`
- **Use Case**: Improve quality of uncertain transcriptions

#### 13. Ingestion Settings - Max Duration
- **Type**: Number input (minutes)
- **User Action**: Enter maximum video duration
- **Setting**: `settings.max_duration_minutes`
- **Backend Integration**: Passed to `/api/ingest/start`
- **Use Case**: Filter out very long videos

#### 14. Preview Button
- **Type**: Action button
- **User Action**: Click to preview account metadata
- **Backend API**: `GET /api/ingest/metadata/{username}`
- **Response**: `AccountMetadata` object with:
  - `username`
  - `total_videos` (number)
  - `videos` (array of video objects with title, views, duration)
- **Display**: Shows preview card with first 10 videos
- **Use Case**: Verify account before ingestion

#### 15. Start Ingestion Button
- **Type**: Primary action button
- **User Action**: Click to start ingestion job
- **Backend API**: `POST /api/ingest/start`
- **Payload**:
  ```json
  {
    "usernames": ["creator1", "creator2"],
    "filters": {
      "last_n_videos": 10,
      "history_start": 0.0,
      "history_end": 1.0,
      "required_category": "Health",
      "required_tags": ["nutrition", "fitness"],
      "skip_no_speech": true,
      "only_with_speech": false
    },
    "settings": {
      "whisper_mode": "balanced",
      "skip_existing": true,
      "retranscribe_low_confidence": false,
      "max_duration_minutes": 10
    }
  }
  ```
- **Response**: `{ job_id, status, message }`
- **Effect**: Starts backend ingestion process
- **Use Case**: Begin bulk account ingestion

#### 16. Job Status Polling
- **Type**: Automatic polling (1 second interval)
- **Trigger**: Starts when ingestion begins
- **Backend API**: `GET /api/ingest/status/{job_id}`
- **Response**: Complete `IngestionJob` object with:
  - `job_id`
  - `status` (queued/downloading/transcribing/complete/failed/etc.)
  - `accounts` (array of account progress)
  - `created_at`, `started_at`, `completed_at`
  - `total_duration_seconds`
- **Update Frequency**: Every 1 second while job is active
- **Stops When**: Job status is complete/cancelled/failed
- **Use Case**: Real-time progress monitoring

#### 17. Pause Ingestion Button
- **Type**: Action button (shown during active ingestion)
- **User Action**: Click to pause current job
- **Backend API**: `POST /api/ingest/pause/{job_id}`
- **Response**: `{ status }`
- **Use Case**: Temporarily halt ingestion

#### 18. Resume Ingestion Button
- **Type**: Action button (shown when job is paused)
- **User Action**: Click to resume paused job
- **Backend API**: `POST /api/ingest/resume/{job_id}`
- **Response**: `{ status }`
- **Effect**: Restarts polling
- **Use Case**: Continue paused ingestion

#### 19. Cancel Ingestion Button
- **Type**: Action button (shown during active ingestion)
- **User Action**: Click to cancel current job
- **Backend API**: `POST /api/ingest/cancel/{job_id}`
- **Response**: `{ status }`
- **Effect**: Stops polling, marks job as cancelled
- **Use Case**: Abort ingestion completely

#### 20. Progress Display - Per Account
- **Type**: Progress cards
- **Display**: For each account in job:
  - Username
  - Status (queued/downloading/transcribing/complete/failed)
  - Total videos found
  - Filtered videos (after applying filters)
  - Processed videos (successfully transcribed)
  - Skipped videos (already existed)
  - Failed videos (errors)
  - Current video being processed (if active)
  - Error message (if failed)
- **Backend API**: None (displays polled data)
- **Use Case**: Monitor per-account ingestion progress

#### 21. Post-Ingestion Actions
- **Type**: Action button group (shown when job complete)
- **Buttons**:
  1. **Search Semantically**: Navigate to `/search`
  2. **View Topics**: Navigate to `/library`
  3. **Export Results**: Download JSON file
- **Backend API**: None (navigation and local export)
- **Use Case**: Next steps after ingestion completes

#### 22. Export Results Button
- **Type**: Download button
- **User Action**: Click to download job results as JSON
- **Processing**: Client-side JSON serialization and download
- **File**: `ingestion_{job_id}.json`
- **Backend API**: None
- **Use Case**: Save ingestion report for records

---

## Page 7: Transcripts Page (Placeholder)
**Route**: `/transcripts`  
**File**: `src/pages/TranscriptsPage.tsx`

### Features
- **Status**: Coming soon placeholder
- **Display**: Empty state message
- **Backend API**: None
- **Use Case**: Future transcript browser feature

---

## Summary of Backend API Endpoints Used

### Search & Browse
1. `GET /api/accounts` - List all creators
2. `GET /api/accounts/{username}/tags` - Get creator topics
3. `GET /api/accounts/{username}/category` - Get creator categories
4. `POST /api/search/semantic` - Semantic search
5. `GET /api/search/filter-options` - Get available filters
6. `GET /api/transcript/{username}/{videoId}` - Get transcript with highlights

### System Management
7. `GET /api/verify/system` - Get system status
8. `POST /api/verify/system` - Re-verify system

### Ingestion Pipeline
9. `POST /api/ingest/start` - Start ingestion job
10. `GET /api/ingest/status/{job_id}` - Get job status
11. `GET /api/ingest/jobs` - List all jobs (not used in current UI)
12. `POST /api/ingest/pause/{job_id}` - Pause job
13. `POST /api/ingest/resume/{job_id}` - Resume job
14. `POST /api/ingest/cancel/{job_id}` - Cancel job
15. `GET /api/ingest/metadata/{username}` - Preview account metadata

---

## Expected Backend Behaviors

### On Ingestion Start
1. Backend creates job with unique `job_id`
2. Returns immediately with job details
3. Starts async processing:
   - Fetches TikTok account metadata
   - Applies video filters (count, history, category, tags, speech)
   - Downloads videos
   - Transcribes with Whisper (using selected mode)
   - Extracts topics using `AccountTopicManager`
   - Creates embeddings using `TranscriptIndexer`
   - Updates job status throughout

### On Ingestion Complete
1. Job status changes to "complete"
2. All accounts show final statistics
3. Topics are extracted and saved
4. Embeddings are indexed for semantic search
5. Videos are immediately searchable via `/api/search/semantic`

### On Search
1. Backend performs semantic search using embeddings
2. Applies filters (creators, tags, category, min_score)
3. Returns top 200 results sorted by relevance
4. Each result includes snippet with context

### On Transcript View
1. Backend loads transcript file
2. If query parameter provided:
   - Highlights all matching segments
   - Returns `highlighted_count`
3. Returns segments with timestamps

---

## User Flows

### Flow 1: Ingest New Creator
1. Navigate to `/ingest`
2. Enter username (single or bulk)
3. Optionally configure filters (video count, categories, topics)
4. Select Whisper mode (quality/speed tradeoff)
5. Click "Start Ingestion"
6. Monitor real-time progress
7. Wait for "complete" status
8. Click "Search Semantically" to find content

### Flow 2: Semantic Search
1. Navigate to `/search`
2. Enter search query (concept/idea)
3. Optionally apply filters (creators, tags, category, score)
4. Review results
5. Click "Open At Timestamp" on interesting result
6. View full transcript with highlights

### Flow 3: Browse Library
1. Navigate to `/library`
2. Optionally search/filter creators
3. Click creator card
4. View topics and categories
5. Explore content distribution

### Flow 4: Monitor System
1. Navigate to `/dashboard`
2. View system metrics
3. Click "Re-verify System" to refresh
4. Check status (healthy/degraded/error)

---

## Notes
- All timestamps in transcripts are in `MM:SS` format
- Search results include `score` (relevance from 0.0 to 1.0)
- Ingestion is idempotent (safe to re-run with `skip_existing: true`)
- Frontend uses 1-second polling for job status (not websockets)
- All API calls use JSON content-type
- Error handling uses toast notifications
