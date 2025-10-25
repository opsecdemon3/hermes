#!/bin/bash

echo "=========================================="
echo "Testing Full Ingestion Pipeline"
echo "=========================================="
echo ""

# Test account (use a small one for testing)
TEST_USER="testaccount"

echo "1. Starting ingestion via API..."
JOB_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/ingest/start" \
  -H "Content-Type: application/json" \
  -d "{
    \"usernames\": [\"$TEST_USER\"],
    \"filters\": {
      \"last_n_videos\": 2
    },
    \"settings\": {
      \"whisper_mode\": \"tiny\",
      \"skip_existing\": false
    }
  }")

echo "Response: $JOB_RESPONSE"
echo ""

# Extract job ID
JOB_ID=$(echo $JOB_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null)

if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to create job"
    exit 1
fi

echo "✅ Job created: $JOB_ID"
echo ""

echo "2. Monitoring progress..."
for i in {1..60}; do
    STATUS=$(curl -s "http://localhost:8000/api/ingest/status/$JOB_ID")
    
    JOB_STATUS=$(echo $STATUS | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    
    echo "   Status: $JOB_STATUS"
    
    if [ "$JOB_STATUS" = "complete" ] || [ "$JOB_STATUS" = "failed" ]; then
        echo ""
        echo "Final status:"
        echo $STATUS | python3 -m json.tool
        break
    fi
    
    sleep 2
done

echo ""
echo "3. Checking results..."
echo ""

# Check if transcripts were created
if [ -d "accounts/$TEST_USER/transcriptions" ]; then
    TRANSCRIPT_COUNT=$(ls -1 accounts/$TEST_USER/transcriptions/*_transcript.txt 2>/dev/null | wc -l)
    echo "✅ Transcripts created: $TRANSCRIPT_COUNT"
else
    echo "❌ No transcriptions directory"
fi

# Check if topics were extracted
if [ -d "accounts/$TEST_USER/topics" ]; then
    TOPIC_COUNT=$(ls -1 accounts/$TEST_USER/topics/*_tags.json 2>/dev/null | wc -l)
    echo "✅ Topics extracted: $TOPIC_COUNT"
else
    echo "❌ No topics directory"
fi

# Check if embeddings were created
if [ -f "data/search/embeddings.jsonl" ]; then
    EMBEDDING_COUNT=$(wc -l < data/search/embeddings.jsonl)
    echo "✅ Embeddings created: $EMBEDDING_COUNT lines"
else
    echo "❌ No embeddings file"
fi

# Check index.json
if [ -f "accounts/$TEST_USER/index.json" ]; then
    echo "✅ Index.json created"
    PROCESSED_COUNT=$(cat accounts/$TEST_USER/index.json | python3 -c "import sys, json; print(len(json.load(sys.stdin)['processed_videos']))" 2>/dev/null)
    echo "   Processed videos in index: $PROCESSED_COUNT"
else
    echo "❌ No index.json"
fi

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
