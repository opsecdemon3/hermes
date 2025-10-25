# TikTalk - Full Stack Setup

## Quick Start

### Start Backend API
```bash
cd /path/to/Tiktok-scraping-main
python3 api_server.py --port 8000
```

### Start Frontend UI
```bash
cd /path/to/Tiktok-scraping-main/synapse-ai-learning-main
npm install  # First time only
npm run dev
```

### Access Application
- **Frontend UI:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## What This System Does

**TikTalk** is a semantic search engine for TikTok transcripts with:
- 🎙️ **Whisper Transcription** - Converts TikTok videos to text
- 🏷️ **Topic Extraction** - Identifies keywords and categorizes content
- 🔍 **Semantic Search** - FAISS-powered similarity search across all transcripts
- 📝 **Context Viewing** - Jump to specific timestamps with surrounding context
- 🌐 **Web UI** - React frontend for browsing and searching
- 🛠️ **CLI Tools** - Command-line scripts for power users

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React/Vite Frontend                      │
│                   (synapse-ai-learning-main/)                │
│  • Library Page - Browse creators                           │
│  • Search Page - Semantic search                            │
│  • Transcript Page - View with context                      │
│  • Dashboard - System stats                                 │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API (CORS-enabled)
                     │
┌────────────────────▼────────────────────────────────────────┐
│                     FastAPI Backend                          │
│                      (api_server.py)                         │
│  • GET /api/accounts                                        │
│  • POST /api/search/semantic                                │
│  • GET /api/transcript/{username}/{video_id}                │
│  • GET /api/verify/system                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┬────────────┐
        │                         │            │
┌───────▼───────┐     ┌──────────▼──────┐   ┌▼──────────┐
│  Transcripts  │     │  FAISS Index    │   │  Topics   │
│  (accounts/)  │     │  (data/search/) │   │ (topics/) │
│               │     │                 │   │           │
│ • Whisper     │     │ • 162 vectors   │   │ • KeyBERT │
│ • .txt files  │     │ • Embeddings    │   │ • Category│
└───────────────┘     └─────────────────┘   └───────────┘
```

---

## Features

### ✅ Working Features
- [x] Multi-video transcription (Whisper)
- [x] Topic extraction (KeyBERT)
- [x] Semantic search (FAISS + sentence-transformers)
- [x] Timestamp-based context expansion
- [x] CLI tools (ingest, search, show)
- [x] REST API with CORS
- [x] React UI with routing
- [x] Loading states and error handling

### 📊 Current Data
- **3 Creators** ingested
- **6 Transcripts** created
- **162 Vector embeddings** indexed
- **30 Topics** extracted

---

## Developer Workflows

### Workflow 1: Ingest New Creator (CLI)
```bash
# Ingest TikTok account
python3 scripts/ingest_account.py --user newcreator --max-videos 10

# Extract topics
python3 scripts/extract_topics.py --user newcreator

# Index for search
python3 scripts/search_semantic.py --index-all

# Now visible in UI automatically
```

### Workflow 2: Search from UI
1. Open http://localhost:5173/search
2. Enter query: "meaning of life"
3. Click result to view transcript at timestamp
4. Context window shows surrounding sentences

### Workflow 3: Browse Creators
1. Open http://localhost:5173/library
2. See all creators with categories and topics
3. Filter by name or category
4. Click to view creator details

---

## Documentation

- **QUICKSTART.md** - Get started in 2 minutes (CLI usage)
- **VALIDATION_REPORT.md** - Full system validation report
- **FRONTEND_INTEGRATION_COMPLETE.md** - Frontend/backend integration details
- **VERIFICATION_COMPLETE.md** - End-to-end test results

---

## Requirements

### Backend
- Python 3.12+
- Dependencies: `pip install -r requirements.txt`
  - faster-whisper
  - sentence-transformers
  - faiss-cpu
  - fastapi
  - keybert

### Frontend
- Node.js 18+
- npm or yarn
- Dependencies: `npm install`

---

## Environment Variables

### Backend (.env in root)
```bash
# No frontend-specific config needed
```

### Frontend (synapse-ai-learning-main/.env)
```bash
VITE_API_BASE=http://localhost:8000
```

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/accounts` | GET | List all creators |
| `/api/accounts/{username}/tags` | GET | Get creator tags |
| `/api/accounts/{username}/category` | GET | Get creator category |
| `/api/search/semantic` | POST | Semantic search |
| `/api/transcript/{username}/{video_id}` | GET | Get transcript |
| `/api/verify/system` | GET | System health |

Full API docs: http://localhost:8000/docs

---

## Testing

### Test Backend
```bash
# List creators
curl http://localhost:8000/api/accounts

# Search
curl -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "meaning", "top_k": 3}'

# Get transcript
curl "http://localhost:8000/api/transcript/beabettermandaily/7563374738840571167?jump=00:10"
```

### Test Frontend
1. Open http://localhost:5173
2. Navigate through pages
3. Check browser console for errors
4. Verify data loads from backend

---

## Troubleshooting

### Backend won't start
```bash
# Check port is free
lsof -i :8000

# Kill existing process
pkill -f api_server.py

# Restart
python3 api_server.py --port 8000
```

### Frontend can't connect
```bash
# Verify backend is running
curl http://localhost:8000/api/accounts

# Check .env file exists
cat synapse-ai-learning-main/.env

# Restart frontend
cd synapse-ai-learning-main
npm run dev
```

### Empty search results
```bash
# Rebuild search index
python3 scripts/search_semantic.py --index-all
```

---

## CLI Tools (Still Work!)

```bash
# Ingest account
python3 scripts/ingest_account.py --user kwrt_

# Extract topics
python3 scripts/extract_topics.py --user kwrt_

# Search
python3 scripts/search_semantic.py "meaning"

# View transcript
python3 scripts/show_transcript.py --video 7563374738840571167 \
  --username beabettermandaily --jump 00:10
```

**CLI and UI work independently.**

---

## Project Status

✅ **Backend:** Fully functional  
✅ **Frontend:** Integrated with backend  
✅ **CLI Tools:** Working  
✅ **Documentation:** Complete  
✅ **Testing:** Validated  

**Ready for use!**

---

## Next Steps

1. **Install Node.js/npm** if not present
2. **Start backend:** `python3 api_server.py`
3. **Start frontend:** `cd synapse-ai-learning-main && npm run dev`
4. **Ingest more creators** to expand dataset
5. **Use the UI** or CLI tools as needed

---

**Project:** TikTalk  
**Status:** Production Ready  
**Date:** October 22, 2025
