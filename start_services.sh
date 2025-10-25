#!/bin/bash

# Startup script for TikTok Scraping System
# This ensures both backend and frontend stay running

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/Users/ronen/Downloads/Tiktok-scraping-main copy 5"

echo -e "${GREEN}=== TikTok Scraping System Startup ===${NC}"

# Kill any existing processes
echo -e "${YELLOW}Stopping existing services...${NC}"
pkill -9 -f "api_server.py" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
sleep 2

# Start backend
echo -e "${GREEN}Starting backend API server on port 8000...${NC}"
cd "$PROJECT_DIR"
nohup python3 api_server.py --port 8000 > api_server.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}Backend started with PID: $BACKEND_PID${NC}"

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/accounts > /dev/null 2>&1; then
        echo -e "${GREEN}Backend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Backend failed to start!${NC}"
        exit 1
    fi
    sleep 1
done

# Start frontend
echo -e "${GREEN}Starting frontend dev server on port 5001...${NC}"
cd "$PROJECT_DIR/synapse-ai-learning-main"
nohup npm run dev > vite.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started with PID: $FRONTEND_PID${NC}"

# Wait for frontend to be ready
echo -e "${YELLOW}Waiting for frontend to be ready...${NC}"
for i in {1..30}; do
    if lsof -nP -iTCP:5001 -sTCP:LISTEN > /dev/null 2>&1; then
        echo -e "${GREEN}Frontend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Frontend failed to start!${NC}"
        exit 1
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}=== All services started successfully! ===${NC}"
echo -e "${GREEN}Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}Frontend: http://localhost:5001${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend:  tail -f $PROJECT_DIR/api_server.log"
echo -e "  Frontend: tail -f $PROJECT_DIR/synapse-ai-learning-main/vite.log"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo -e "  pkill -f 'api_server.py'"
echo -e "  pkill -f 'vite'"
echo ""

# Keep the script running to monitor services
echo -e "${YELLOW}Monitoring services (Ctrl+C to stop)...${NC}"
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend stopped unexpectedly!${NC}"
        exit 1
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}Frontend stopped unexpectedly!${NC}"
        exit 1
    fi
    sleep 5
done
