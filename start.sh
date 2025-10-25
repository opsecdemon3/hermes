#!/bin/bash

# Simple service starter that STAYS RUNNING
# This version uses disown to fully detach processes

PROJECT_DIR="/Users/ronen/Downloads/Tiktok-scraping-main copy 5"

echo "=== Stopping existing services ==="
pkill -9 -f "api_server.py" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
sleep 2

echo "=== Starting Backend on port 8000 ==="
cd "$PROJECT_DIR"
nohup python3 api_server.py --port 8000 > api_server.log 2>&1 &
BACKEND_PID=$!
disown $BACKEND_PID
echo "Backend PID: $BACKEND_PID"

echo "=== Starting Frontend on port 5001 ==="
cd "$PROJECT_DIR/synapse-ai-learning-main"
nohup npm run dev > vite.log 2>&1 &
FRONTEND_PID=$!
disown $FRONTEND_PID
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "=== Waiting for services to start (5 seconds) ==="
sleep 5

echo ""
echo "=== Checking if services are running ==="
if lsof -nP -iTCP:8000 -sTCP:LISTEN > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
else
    echo "❌ Backend is NOT running! Check $PROJECT_DIR/api_server.log"
    exit 1
fi

if lsof -nP -iTCP:5001 -sTCP:LISTEN > /dev/null 2>&1; then
    echo "✅ Frontend is running on port 5001"
else
    echo "❌ Frontend is NOT running! Check $PROJECT_DIR/synapse-ai-learning-main/vite.log"
    exit 1
fi

echo ""
echo "=== All services started successfully! ==="
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5001"
echo ""
echo "Logs:"
echo "  Backend:  tail -f $PROJECT_DIR/api_server.log"
echo "  Frontend: tail -f $PROJECT_DIR/synapse-ai-learning-main/vite.log"
echo ""
echo "To stop:"
echo "  pkill -f 'api_server.py'"
echo "  pkill -f 'vite'"
echo ""
echo "Services are now detached and will continue running."
