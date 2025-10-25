#!/bin/bash
# Test Ingestion System - All Features

echo "=================================================="
echo "🧪 TESTING INGESTION SYSTEM"
echo "=================================================="
echo ""

BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Filter Options
echo "📋 Test 1: Get Filter Options"
response=$(curl -s "$BASE_URL/api/search/filter-options")
creators=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data['creators']))")
if [ "$creators" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Found $creators creators"
else
    echo -e "${RED}❌ FAIL${NC} - No creators found"
fi
echo ""

# Test 2: Get Account Metadata
echo "📊 Test 2: Get Account Metadata"
response=$(curl -s "$BASE_URL/api/ingest/metadata/beabettermandaily")
total_videos=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('total_videos', 0))")
if [ "$total_videos" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Found $total_videos videos for beabettermandaily"
else
    echo -e "${RED}❌ FAIL${NC} - Failed to fetch metadata"
fi
echo ""

# Test 3: Start Ingestion Job (with filters)
echo "🚀 Test 3: Start Ingestion Job (Last 5 videos)"
response=$(curl -s -X POST "$BASE_URL/api/ingest/start" \
  -H "Content-Type: application/json" \
  -d '{
    "usernames": ["beabettermandaily"],
    "filters": {"last_n_videos": 5},
    "settings": {"whisper_mode": "fast", "skip_existing": true}
  }')
job_id=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('job_id', ''))")
if [ -n "$job_id" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Job created: $job_id"
else
    echo -e "${RED}❌ FAIL${NC} - Failed to create job"
    exit 1
fi
echo ""

# Test 4: Poll Job Status
echo "⏳ Test 4: Poll Job Status (waiting for completion)"
for i in {1..10}; do
    sleep 1
    response=$(curl -s "$BASE_URL/api/ingest/status/$job_id")
    status=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('status', ''))")
    
    if [ "$status" == "complete" ]; then
        echo -e "${GREEN}✅ PASS${NC} - Job completed successfully"
        
        # Extract stats
        total=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['accounts'][0]['total_videos'])")
        filtered=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['accounts'][0]['filtered_videos'])")
        processed=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['accounts'][0]['processed_videos'])")
        
        echo "   📊 Stats:"
        echo "      Total videos: $total"
        echo "      Filtered to: $filtered"
        echo "      Processed: $processed"
        break
    elif [ "$status" == "failed" ]; then
        echo -e "${RED}❌ FAIL${NC} - Job failed"
        break
    else
        echo "   Status: $status (attempt $i/10)"
    fi
done
echo ""

# Test 5: List All Jobs
echo "📜 Test 5: List All Jobs"
response=$(curl -s "$BASE_URL/api/ingest/jobs")
job_count=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('jobs', [])))")
if [ "$job_count" -gt 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Found $job_count job(s) in history"
else
    echo -e "${YELLOW}⚠️  WARN${NC} - No jobs in history"
fi
echo ""

# Test 6: Test with Multiple Filters
echo "🎯 Test 6: Start Job with Multiple Filters"
response=$(curl -s -X POST "$BASE_URL/api/ingest/start" \
  -H "Content-Type: application/json" \
  -d '{
    "usernames": ["beabettermandaily"],
    "filters": {
      "last_n_videos": 3,
      "required_category": "Health",
      "skip_no_speech": true
    },
    "settings": {"whisper_mode": "balanced", "skip_existing": true}
  }')
job_id2=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('job_id', ''))")
if [ -n "$job_id2" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Multi-filter job created: $job_id2"
    
    # Wait for completion
    sleep 3
    response=$(curl -s "$BASE_URL/api/ingest/status/$job_id2")
    status=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('status', ''))")
    echo "   Final status: $status"
else
    echo -e "${RED}❌ FAIL${NC} - Failed to create multi-filter job"
fi
echo ""

# Test 7: Verify Idempotency (re-run same job)
echo "♻️  Test 7: Test Idempotency (re-run same videos)"
response=$(curl -s -X POST "$BASE_URL/api/ingest/start" \
  -H "Content-Type: application/json" \
  -d '{
    "usernames": ["beabettermandaily"],
    "filters": {"last_n_videos": 5},
    "settings": {"skip_existing": true}
  }')
job_id3=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('job_id', ''))")

sleep 3
response=$(curl -s "$BASE_URL/api/ingest/status/$job_id3")
processed=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['accounts'][0]['processed_videos'])")
skipped=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['accounts'][0]['skipped_videos'])")

if [ "$skipped" -ge "$processed" ]; then
    echo -e "${GREEN}✅ PASS${NC} - Idempotency working (skipped: $skipped, processed: $processed)"
else
    echo -e "${YELLOW}⚠️  WARN${NC} - Some videos were reprocessed"
fi
echo ""

# Summary
echo "=================================================="
echo "✅ ALL TESTS COMPLETED"
echo "=================================================="
echo ""
echo "Frontend available at: http://localhost:5002/ingest"
echo "Backend API docs at: http://localhost:8000/docs"
echo ""
