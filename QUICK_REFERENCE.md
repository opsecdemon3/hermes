# 🚀 Quick Reference - 2-Layer Ontology

## 📂 File Structure

```
accounts/{account}/topics/
├── {video_id}_tags.json        # Per-video tags
├── account_tags.json           # Account-level aggregated tags
└── account_category.json       # Single broad category
```

---

## 🖥️ CLI Commands

### Extract Tags & Classify
```bash
# Extract tags from all videos + classify account
python scripts/extract_topics.py --user kwrt_

# Force re-extract (overwrite existing)
python scripts/extract_topics.py --user kwrt_ --force
```

### View Results

```bash
# View broad category
python scripts/list_topics.py --user kwrt_ --category

# View account tags (default)
python scripts/list_topics.py --user kwrt_

# View per-video tags
python scripts/list_topics.py --user kwrt_ --by-video

# View everything
python scripts/list_topics.py --user kwrt_ --all

# Export to JSON
python scripts/list_topics.py --user kwrt_ --export kwrt_data.json
```

### Verify
```bash
# Verify data integrity
python scripts/verify_ingestion.py --account kwrt_
```

---

## 🌐 API Endpoints (v3.0.0)

### Account Category
```bash
GET /api/accounts/{username}/category

# Response:
{
  "category": "Philosophy",
  "confidence": 0.708,
  "all_scores": {...}
}
```

### Account Tags
```bash
GET /api/accounts/{username}/tags?top_n=20&min_frequency=2

# Response:
{
  "total_tags": 30,
  "total_videos": 3,
  "tags": [...]
}
```

### Video Tags
```bash
GET /api/accounts/{username}/tags/by-video
GET /api/accounts/{username}/tags/video/{video_id}
```

---

## 📊 Predefined Categories

```
Philosophy          Psychology         Self-Improvement
Spirituality        Business           Health
Tech                Politics           History
Creativity          Education          Entertainment
Music               Art                Science
```

---

## 🎯 Two-Layer Filtering

| Layer | Purpose | Example Query |
|-------|---------|---------------|
| **Category** | Filter creators | "Show all Philosophy creators" |
| **Tags** | Filter videos | "Videos about belief systems" |
| **Combined** | Both | "Philosophy creators + meditation videos" |

---

## ✅ Quick Test

```bash
# 1. Ingest account
python scripts/ingest_account.py --user kwrt_ --max-videos 5

# 2. Extract tags + classify
python scripts/extract_topics.py --user kwrt_

# 3. View category
python scripts/list_topics.py --user kwrt_ --category

# 4. Verify
python scripts/verify_ingestion.py --account kwrt_
```

Expected output:
```
Category: Philosophy (70.8%)
Tags: 30 unique
Videos: 3
✅ Perfect data integrity!
```

---

## 🔄 Migration from Umbrella System

If you have old `umbrella_topics.json` files:

```bash
# Remove old umbrella files
find accounts -name "umbrella_topics.json" -delete
find accounts -name "*_topics.json" -delete
find accounts -name "account_topics.json" -delete

# Re-extract with new system
python scripts/extract_topics.py --user {username} --force
```

---

## 💡 Tips

1. **Category confidence >0.7** = strong match
2. **Use `--all` flag** to see complete picture
3. **Tag frequency** = how many videos have that tag
4. **Combined score** = frequency × avg_score × engagement

---

*Version: 3.0.0*  
*Last Updated: October 21, 2025*


