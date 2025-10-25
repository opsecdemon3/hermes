# TikTok Transcript System - Quickstart Guide
## Get Started in Under 2 Minutes

---

## Prerequisites

You need Python 3.12+ and these packages installed:
```bash
pip install -r requirements.txt
```

---

## Basic Usage (4 Simple Steps)

### 1. Ingest a TikTok Account
```bash
python3 scripts/ingest_account.py --user kwrt_ --max-videos 10
```
**What it does:** Downloads videos, transcribes with Whisper, saves to `accounts/kwrt_/`

**Re-running is safe!** It only processes new videos (idempotent).

---

### 2. Extract Topics
```bash
python3 scripts/extract_topics.py --user kwrt_
```
**What it does:** Extracts keywords and categorizes the account (Philosophy, Health, Business, etc.)

**Output:** `accounts/kwrt_/topics/` with account_tags.json and account_category.json

---

### 3. Index for Semantic Search
```bash
python3 scripts/search_semantic.py --index-all
```
**What it does:** Creates FAISS embeddings from all transcripts

**Run once per new account**, or when you add more videos.

---

### 4. Search!
```bash
python3 scripts/search_semantic.py "meaning of life"
```
**What it does:** Finds relevant segments across all videos with timestamps

**Example Output:**
```
1. Score: 0.353
   👤 @kwrt_ — 📹 7557947251092409613 — ⏰ 00:41
   📝 Snippet: what does it mean to be alive and why are we alive...
   🔗 python scripts/show_transcript.py --video 7557947251092409613 --username kwrt_ --jump 00:41
```

---

## View Full Context

When you find a good result, jump to the full transcript:

```bash
python3 scripts/show_transcript.py --video 7557947251092409613 --username kwrt_ --jump 00:41 --context 5
```

**What it does:** Shows the matched sentence (highlighted) with 5 sentences before/after for context.

---

## Complete Example Workflow

```bash
# 1. Ingest account
python3 scripts/ingest_account.py --user kwrt_

# 2. Extract topics
python3 scripts/extract_topics.py --user kwrt_

# 3. Index for search
python3 scripts/search_semantic.py --index-all

# 4. Search
python3 scripts/search_semantic.py "meaning"

# 5. View context (use video_id and timestamp from search results)
python3 scripts/show_transcript.py --video 7557947251092409613 --username kwrt_ --jump 00:41
```

**Time:** ~5 minutes for 10 videos

---

## Optional: Start API Server

```bash
python3 api_server.py --port 8000
```

**Access at:** http://localhost:8000/docs

**Key Endpoints:**
- `POST /api/search/semantic` - Search transcripts
- `GET /api/transcript/{username}/{video_id}` - Get full transcript with jump
- `GET /api/accounts/{username}/tags` - Get account topics
- `GET /api/accounts/{username}/category` - Get account category

**Example API Call:**
```bash
curl -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "meaning", "top_k": 5}'
```

---

## Common Commands Reference

| Task | Command |
|------|---------|
| Ingest account | `python3 scripts/ingest_account.py --user USERNAME` |
| Extract topics | `python3 scripts/extract_topics.py --user USERNAME` |
| Index for search | `python3 scripts/search_semantic.py --index-all` |
| Search | `python3 scripts/search_semantic.py "QUERY"` |
| View transcript | `python3 scripts/show_transcript.py --video VIDEO_ID --username USERNAME --jump MM:SS` |
| List topics | `python3 scripts/list_topics.py --user USERNAME` |
| View category | `python3 scripts/list_topics.py --user USERNAME --category` |
| Start API | `python3 api_server.py` |

---

## File Locations

After running these commands, here's where your data is:

```
accounts/
  └── kwrt_/
      ├── index.json                          # Tracks what's been processed
      ├── transcriptions/
      │   └── 7557947251092409613_transcript.txt
      └── topics/
          ├── 7557947251092409613_tags.json   # Video-level topics
          ├── account_tags.json               # All tags ranked
          └── account_category.json           # Account category

data/
  └── search/
      ├── index.faiss                         # Vector search index
      └── embeddings.jsonl                    # Metadata for search
```

---

## Tips & Tricks

### Re-running is Safe
All commands are **idempotent**. Running twice does zero duplicate work:
- Ingestion skips already-transcribed videos
- Topic extraction skips videos that already have topics
- Search indexing skips already-indexed transcripts

### Use --with-topics Flag
Skip a step by combining ingestion + topic extraction:
```bash
python3 scripts/ingest_account.py --user kwrt_ --with-topics
```

### Limit Videos (For Testing)
```bash
python3 scripts/ingest_account.py --user kwrt_ --max-videos 5
```

### Search with More Results
```bash
python3 scripts/search_semantic.py "meaning" --top-k 10
```

### View All Account Topics
```bash
python3 scripts/list_topics.py --user kwrt_ --all
```

---

## Troubleshooting

### "No videos found"
→ Check username (try with/without @)  
→ Account might be private

### "No results found" when searching
→ Run `python3 scripts/search_semantic.py --index-all` first

### "Transcript not found"
→ Make sure you ingested the account first  
→ Check the username matches

### Import errors
→ Run `pip install -r requirements.txt`

---

## That's It!

You now have a fully functional TikTok transcript system with:
- ✅ Video transcription (Whisper)
- ✅ Topic extraction (KeyBERT)
- ✅ Semantic search (FAISS)
- ✅ Context expansion (timestamp jumping)
- ✅ REST API (FastAPI)

**Questions?** Check `VALIDATION_REPORT.md` for detailed technical info.

---

## Starting the Web UI (Frontend + Backend)

### Use the Start Script (RECOMMENDED)

```bash
./start.sh
```

This script:
- ✅ Kills any existing services
- ✅ Starts backend API (port 8000) with proper detachment
- ✅ Starts frontend UI (port 5001) with proper detachment
- ✅ Verifies both are listening
- ✅ Processes stay running even after you close the terminal

### Manual Start (if needed)

```bash
# Kill old processes
pkill -9 -f "api_server.py"
pkill -9 -f "vite"
sleep 2

# Start backend
nohup python3 api_server.py --port 8000 > api_server.log 2>&1 & disown

# Start frontend
cd synapse-ai-learning-main
nohup npm run dev > vite.log 2>&1 & disown
cd ..

# Verify (wait 3 seconds)
sleep 3
lsof -nP -iTCP:8000,5001 -sTCP:LISTEN
```

**CRITICAL: Always include `disown` to prevent process termination!**

### Access the Application

- **Frontend UI:** http://localhost:5001
- **Backend API:** http://localhost:8000/api/accounts

### If You See a Blank Page

1. Check if Vite is running: `lsof -nP -iTCP:5001 -sTCP:LISTEN`
2. Check Vite logs: `tail -50 synapse-ai-learning-main/vite.log`
3. Check browser console (F12) for JavaScript errors
4. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)
5. Restart with `./start.sh`

See `FRONTEND_BLANK_PAGE_FIX.md` for detailed troubleshooting.

---

**Last Updated:** October 23, 2025  
**System Status:** ✅ Fully Operational
