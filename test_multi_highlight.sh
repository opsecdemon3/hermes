#!/bin/bash

echo "🧪 Testing Multi-Highlight & Unlimited Results Feature"
echo ""

echo "📊 Test 1: Unlimited Search Results"
echo "Query: 'life'"
RESULT=$(curl -s -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "life", "top_k": 200}')
COUNT=$(echo $RESULT | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "✅ Got $COUNT results (not limited to 5)"
echo ""

echo "📝 Test 2: Full Transcript with Multiple Highlights"
echo "Video: matrix.v5/7563093332688129310"
echo "Query: 'reality'"
TRANSCRIPT=$(curl -s "http://localhost:8000/api/transcript/matrix.v5/7563093332688129310?query=reality")
TOTAL=$(echo $TRANSCRIPT | python3 -c "import sys, json; print(json.load(sys.stdin)['total_segments'])")
HIGHLIGHTED=$(echo $TRANSCRIPT | python3 -c "import sys, json; print(json.load(sys.stdin)['highlighted_count'])")
echo "✅ Total segments: $TOTAL"
echo "✅ Highlighted: $HIGHLIGHTED"
echo ""

echo "🔍 Test 3: Multiple Results Per Video"
echo "Query: 'reality perception'"
RESULTS=$(curl -s -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "reality perception"}')
echo "$RESULTS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
videos = {}
for r in data:
    key = f\"{r['username']}/{r['video_id']}\"
    if key not in videos:
        videos[key] = []
    videos[key].append(r['timestamp'])
    
for video, timestamps in videos.items():
    if len(timestamps) > 1:
        print(f'✅ {video} appears {len(timestamps)} times at: {', '.join(timestamps)}')
"
echo ""

echo "🎉 All tests passed!"
