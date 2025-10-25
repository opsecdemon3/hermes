#!/bin/bash

# Monitor ingestion job progress in real-time
# This shows what the frontend UI is polling

echo "=== Monitoring Ingestion Jobs ==="
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=== Ingestion Jobs Status ($(date '+%H:%M:%S')) ==="
    echo ""
    
    # Get all jobs
    JOBS=$(curl -s http://localhost:8000/api/jobs 2>/dev/null)
    
    if [ -z "$JOBS" ] || [ "$JOBS" = "[]" ]; then
        echo "No active jobs"
    else
        echo "$JOBS" | python3 -m json.tool 2>/dev/null || echo "$JOBS"
    fi
    
    echo ""
    echo "---"
    sleep 1
done
