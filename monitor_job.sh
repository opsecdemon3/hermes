#!/bin/bash

JOB_ID="a5b9611f-4270-4058-bae8-db4e335ec465"

echo "=== Monitoring Job: $JOB_ID ==="
echo ""

for i in {1..60}; do
    clear
    echo "=== Job Status (check $i/60) - $(date '+%H:%M:%S') ==="
    echo ""
    
    STATUS=$(curl -s http://localhost:8000/api/ingest/status/$JOB_ID)
    
    # Extract key info
    echo "$STATUS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Status: {data['status']}\")
print(f\"Overall Progress: {data['overall_progress']}%\")
print(f\"Elapsed: {data['elapsed_seconds']}s\")
print(f\"ETA: {data.get('eta_seconds', 'N/A')}s\")
print()

for acc in data['accounts']:
    print(f\"Account: {acc['username']}\")
    print(f\"  Progress: {acc['overall_progress']}%\")
    print(f\"  Total: {acc['total_videos']}, Filtered: {acc['filtered_videos']}\")
    print(f\"  Processed: {acc['processed_videos']}, Skipped: {acc['skipped_videos']}, Failed: {acc['failed_videos']}\")
    if acc['current_video']:
        cv = acc['current_video']
        print(f\"  Current: [{cv['step']}] {cv['title'][:60]}\")
    print(f\"  Videos completed: {len(acc.get('videos', []))}\")
    print()
" 2>/dev/null || echo "$STATUS" | head -30
    
    # Check if complete
    if echo "$STATUS" | grep -q '"status": "complete"'; then
        echo ""
        echo "✅ Job completed!"
        break
    fi
    
    if echo "$STATUS" | grep -q '"status": "failed"'; then
        echo ""
        echo "❌ Job failed!"
        echo ""
        echo "Full response:"
        echo "$STATUS" | python3 -m json.tool
        break
    fi
    
    sleep 2
done
