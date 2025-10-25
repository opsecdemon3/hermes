# TikTok Transcription Pipeline

A production-ready, idempotent pipeline for transcribing TikTok videos using yt-dlp and OpenAI Whisper.

## ✨ Features

### Core Capabilities
- ✅ **Real AI Transcription** - OpenAI Whisper via faster-whisper
- ✅ **Multi-Account Support** - Process any TikTok account
- ✅ **Idempotent & Resumable** - Skip already-processed videos automatically
- ✅ **Authenticated Scraping** - Optional cookies.txt support
- ✅ **Batch Processing** - Process multiple accounts at once
- ✅ **Smart Speech Detection** - Auto-skip videos with no speech
- ✅ **Data Integrity** - Verification tools included
- ✅ **Progress Tracking** - Real-time progress bars (with tqdm)
- ✅ **CSV Export** - Export results for analysis

### Production Features
- 🔄 **Append-Only** - Only downloads+transcribes new videos
- 💾 **Index Tracking** - `index.json` as source of truth
- 🛡️ **Crash-Resistant** - Saves after each video
- 🚀 **Fast** - Skips unnecessary work
- 📊 **Comprehensive Logging** - Track everything

## 📦 Installation

### 1. System Dependencies

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2. Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Optional: Progress Bars
```bash
pip install tqdm
```

### 4. Verify Installation
```bash
python test_dependencies.py
```

## 🚀 Quick Start

### Single Account Ingestion
```bash
# First run - processes all videos
python scripts/ingest_account.py --user kwrt_

# Second run - only processes new videos (idempotent!)
python scripts/ingest_account.py --user kwrt_
```

### Batch Processing
```bash
# Process multiple accounts
python scripts/batch_ingest.py --users kwrt_ matrix.v5 beabettermandaily

# From file (one username per line)
python scripts/batch_ingest.py --file accounts.txt
```

### Verification
```bash
# Verify data integrity
python scripts/verify_ingestion.py

# Verify specific account
python scripts/verify_ingestion.py --account kwrt_
```

## 📖 Usage Guide

### Basic Ingestion

```bash
# Process account with defaults (10 videos, small model)
python scripts/ingest_account.py --user kwrt_

# Process more videos with larger model
python scripts/ingest_account.py --user kwrt_ --max-videos 50 --model-size medium

# With authentication (see COOKIES_GUIDE.md)
python scripts/ingest_account.py --user kwrt_ --cookies cookies.txt

# Verbose mode for debugging
python scripts/ingest_account.py --user kwrt_ -v
```

### Advanced Options

```bash
python scripts/ingest_account.py \
  --user kwrt_ \
  --max-videos 100 \
  --model-size large \
  --cookies cookies.txt \
  --min-speech 100 \
  --verbose
```

### Batch Ingestion

```bash
# Multiple accounts inline
python scripts/batch_ingest.py --users kwrt_ matrix.v5 beabettermandaily

# From accounts.txt file
python scripts/batch_ingest.py --file accounts.txt --max-videos 20

# With all options
python scripts/batch_ingest.py \
  --file accounts.txt \
  --max-videos 50 \
  --model-size medium \
  --cookies cookies.txt
```

### Legacy Single-Video Mode

The original standalone transcriber is still available:

```bash
python tiktok_transcriber.py --user kwrt_ --max-videos 10
```

## 📁 Directory Structure

```
accounts/
├── kwrt_/
│   ├── index.json                    # Source of truth for processed videos
│   └── transcriptions/
│       ├── 7557947251092409613_transcript.txt
│       ├── 7554580484513205517_transcript.txt
│       └── kwrt__results.json        # Legacy results file
├── matrix.v5/
│   ├── index.json
│   └── transcriptions/
│       └── ...
└── _batch_reports/                    # CSV exports from batch runs
    └── batch_ingestion_20251021_123456.csv
```

## 📊 Output Files

### index.json (Source of Truth)
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

### Transcript Files
```
# Transcription for Video 7557947251092409613
Title: #philosophy #wisdom #life #spirituality
Timestamp: 2025-10-21T07:30:15
==================================================

[Transcribed speech content here...]
```

## 🎯 Idempotent Behavior

The key feature of this pipeline is **idempotency** - running the same command multiple times does zero extra work:

```bash
# First run
$ python scripts/ingest_account.py --user kwrt_
Found 15 total videos
0 already processed → SKIPPED
15 new videos → TRANSCRIBED and SAVED
✅ Completed in 5m 30s

# Second run (immediately after)
$ python scripts/ingest_account.py --user kwrt_
Found 15 total videos
15 already processed → SKIPPED
0 new videos → TRANSCRIBED and SAVED
✅ Completed in 3s

# Third run (after new content posted)
$ python scripts/ingest_account.py --user kwrt_
Found 18 total videos
15 already processed → SKIPPED
3 new videos → TRANSCRIBED and SAVED
✅ Completed in 1m 45s
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Copy template
cp env.example .env

# Edit .env
OUTPUT_DIR=accounts
WHISPER_MODEL_SIZE=small
MAX_VIDEOS=10
MIN_SPEECH_THRESHOLD=50
COOKIES_FILE=cookies.txt  # Optional
```

### Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--user, -u` | Required | TikTok username (with or without @) |
| `--max-videos` | 10 | Maximum videos to fetch per run |
| `--model-size` | small | Whisper model (tiny/small/medium/large) |
| `--cookies` | None | Path to cookies.txt for authentication |
| `--min-speech` | 50 | Minimum chars to consider video has speech |
| `--verbose, -v` | False | Enable debug logging |

## 🤖 Whisper Models

| Model | Size | Speed | Accuracy | RAM | Best For |
|-------|------|-------|----------|-----|----------|
| `tiny` | 39 MB | Fastest | Lower | ~1 GB | Testing, music videos |
| `small` | 244 MB | Fast | Good | ~2 GB | **Recommended** |
| `medium` | 769 MB | Slower | High | ~5 GB | Accents, complex speech |
| `large` | 1.5 GB | Slowest | Best | ~10 GB | Maximum accuracy |

## 🔍 Verification & Quality Control

### Check Data Integrity
```bash
# Verify all accounts
python scripts/verify_ingestion.py

# Output:
# ✅ All accounts have perfect data integrity!
# - 0 missing transcripts
# - 0 duplicate transcripts  
# - 0 orphaned files
```

### Legacy Verification (Transcript Files)
```bash
python verify_transcripts.py --account kwrt_
```

## 🍪 Authentication Setup

For better reliability and to avoid rate limiting, use cookies:

1. **Export cookies** from your browser (see [COOKIES_GUIDE.md](COOKIES_GUIDE.md))
2. **Save as** `cookies.txt`
3. **Use with** `--cookies cookies.txt`

**Quick cookie export:**
- Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

See detailed guide: [COOKIES_GUIDE.md](COOKIES_GUIDE.md)

## 📈 CSV Export

Batch ingestion automatically exports CSV reports:

```csv
account,all_videos,already_processed,newly_processed,newly_skipped,newly_failed,duration,status
kwrt_,15,10,5,0,0,180.5s,success
matrix.v5,20,15,4,1,0,220.3s,success
```

Location: `accounts/_batch_reports/batch_ingestion_TIMESTAMP.csv`

## 🐛 Troubleshooting

### HTTP 403 Errors
- Use cookies.txt for authentication
- Add delays between accounts in batch mode
- Check TikTok hasn't rate-limited your IP

### No Videos Found
- Verify account exists and is public
- Check username spelling (without @)
- Try with cookies.txt

### Transcription Quality Issues
- Use larger model: `--model-size medium` or `--model-size large`
- Check video actually has speech (not just music)
- Adjust `--min-speech` threshold

### Verification Fails
```bash
# Check what's wrong
python scripts/verify_ingestion.py

# Common fixes:
# - Orphaned files: Delete them or re-run ingestion
# - Missing transcripts: Re-run with that video_id
# - Duplicate transcripts: Clean up manually
```

## 📚 Advanced Usage

### Process Specific Number of New Videos
```bash
# Only process up to 5 new videos
python scripts/ingest_account.py --user kwrt_ --max-videos 5
```

### Batch from File
```bash
# Create accounts.txt
cat > accounts.txt << EOF
kwrt_
matrix.v5
beabettermandaily
# Add more accounts here
EOF

# Run batch
python scripts/batch_ingest.py --file accounts.txt
```

### Schedule with Cron
```bash
# Daily at 2 AM
0 2 * * * cd /path/to/project && python scripts/ingest_account.py --user kwrt_

# Weekly batch on Sundays at 3 AM
0 3 * * 0 cd /path/to/project && python scripts/batch_ingest.py --file accounts.txt
```

## 🔬 Testing

Test the system with 3 videos first:

```bash
# Quick test
python scripts/ingest_account.py --user kwrt_ --max-videos 3 --model-size tiny

# Verify
python scripts/verify_ingestion.py --account kwrt_

# Test idempotency (should complete in <5s)
python scripts/ingest_account.py --user kwrt_ --max-videos 3 --model-size tiny
```

## 📝 Requirements

See [requirements.txt](requirements.txt):
- `yt-dlp>=2023.12.30` - TikTok video downloading
- `faster-whisper>=0.10.0` - AI transcription
- `python-dotenv>=1.0.0` - Environment management
- `pandas>=2.1.4` - Data processing
- `numpy>=1.24.4` - Numerical operations
- `tqdm` (optional) - Progress bars

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional video metadata extraction
- Alternative transcription engines
- Web UI for management
- Real-time monitoring dashboard
- Topic extraction (Step 2)

## 📄 License

MIT License - See LICENSE file for details

---

## 🌟 Hermes Phase 0

**NEW:** Hermes is an AI-powered content strategy planner built on top of TikTalk's foundation.

### What is Hermes?

Hermes analyzes top-performing creators and generates personalized content plans tailored to your goals (Growth, Leads, or Sales).

### Quick Start

**Backend:**
```bash
# Hermes is enabled by default
export HERMES_ENABLED=true
python api_server.py

# Access health check
curl http://localhost:8000/api/hermes/health
```

**Frontend:**
```bash
cd synapse-ai-learning-main:frontend

# Enable Hermes UI (default)
export VITE_HERMES_ENABLED=true
npm run dev

# Visit http://localhost:5173/hermes
```

### Feature Flags

- **`HERMES_ENABLED`** (backend) - Enable/disable Hermes API routes (default: `true`)
- **`VITE_HERMES_ENABLED`** (frontend) - Show/hide Hermes UI (default: `true`)
- **`VITE_LABS_ENABLED`** (frontend) - Show/hide experimental Labs section (default: `false`)

### Routes

- `/hermes` - Landing page with product overview
- `/hermes/analyze` - Submit plan generation request
- `/hermes/plan/:id` - View plan status and results
- `/labs/dashboard` - Experimental features (when enabled)

### API Endpoints

- `GET /api/hermes/health` - Health check (no auth)
- `POST /api/hermes/plan` - Submit plan request (requires auth)
- `GET /api/hermes/plans/{id}` - Get plan status (requires auth)
- `POST /api/hermes/insight` - Generate content insight (requires auth)

### Testing

```bash
# Backend tests
pytest tests/test_hermes_phase0.py -v
pytest tests/test_worker_hermes_phase0.py -v

# Frontend tests (requires Cypress)
cd synapse-ai-learning-main:frontend
npx cypress run --spec cypress/e2e/hermes-phase0.cy.ts
```

### Documentation

See [SAAS_PHASE_0_HERMES_SURFACE.md](SAAS_PHASE_0_HERMES_SURFACE.md) for complete Phase 0 documentation, including:
- Architecture decisions
- Full API contracts
- Test coverage report
- Next steps for Phase 1

**Phase 0 Status:** ✅ Surface layer complete (all stubs, no business logic)

---

## ⚠️ Disclaimer

This tool is for educational and research purposes. Please:
- Respect TikTok's Terms of Service
- Only scrape public content
- Use reasonable rate limits
- Don't redistribute scraped content without permission

## 🚀 What's Next?

After ingestion is working, the next steps are:
1. **Step 2: Topic Extraction** - Extract themes from transcripts
2. **Step 3: Semantic Search** - Search transcripts by meaning
3. **Step 4: AI Chat Interface** - Chat with transcript data
4. **Step 5: Analytics Dashboard** - Visualize trends

---

**Made with ❤️ for transparent, idempotent data pipelines**
