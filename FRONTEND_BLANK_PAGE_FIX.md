# Frontend Blank Page Issue - ROOT CAUSE & PERMANENT FIX

## Problem
The frontend shows a blank page intermittently, especially after crashes or restarts.

## Root Causes Identified

### 1. **Process Termination Issue**
- When starting services with `nohup ... &` WITHOUT `disown`, the processes remain attached to the parent shell
- If the parent shell exits or is interrupted (Ctrl+C), the child processes are terminated
- This causes the frontend to stop serving, resulting in a blank page

### 2. **Vite Development Server Instability**
- Vite dev server runs in development mode and can crash if:
  - Port 5001 is already in use
  - Environment variables are not loaded properly
  - The process is interrupted during startup
  - Parent process terminates

### 3. **Missing Process Monitoring**
- No automatic restart mechanism
- No health checks to verify services are running
- Processes can die silently without notification

## Permanent Solution

### Start Services Properly
Always use `nohup ... & disown` to completely detach processes:

```bash
# Backend
cd /Users/ronen/Downloads/Tiktok-scraping-main\ copy\ 5
nohup python3 api_server.py --port 8000 > api_server.log 2>&1 & disown

# Frontend  
cd /Users/ronen/Downloads/Tiktok-scraping-main\ copy\ 5/synapse-ai-learning-main
nohup npm run dev > vite.log 2>&1 & disown
```

### Verify Services After Start
```bash
# Wait for services to start
sleep 3

# Check if ports are listening
lsof -nP -iTCP:8000,5001 -sTCP:LISTEN

# Test backend API
curl -s http://localhost:8000/api/accounts | head -20

# Test frontend (should return HTML with <div id="root">)
curl -s http://localhost:5001 | grep -A 5 "root"
```

### Service Management Script
Use the provided `start_services.sh` script, but run it in detached mode:

```bash
# Start script in background
nohup /path/to/start_services.sh > startup.log 2>&1 &

# Or use screen/tmux for interactive monitoring
screen -dmS tiktok-services /path/to/start_services.sh
```

## Quick Troubleshooting

### If Frontend Shows Blank Page:

1. **Check if Vite is running:**
   ```bash
   lsof -nP -iTCP:5001 -sTCP:LISTEN
   ```

2. **Check Vite logs:**
   ```bash
   tail -50 /Users/ronen/Downloads/Tiktok-scraping-main\ copy\ 5/synapse-ai-learning-main/vite.log
   ```

3. **Check what's being served:**
   ```bash
   curl -s http://localhost:5001 | head -20
   ```
   - Should see `<!DOCTYPE html>` and `<div id="root"></div>`
   - If empty or connection refused, Vite is not running

4. **Check browser console:**
   - Open browser DevTools (F12)
   - Look for JavaScript errors
   - Check Network tab for failed requests to backend API

5. **Restart properly:**
   ```bash
   # Kill existing processes
   pkill -9 -f "vite"
   pkill -9 -f "api_server.py"
   
   # Wait
   sleep 2
   
   # Restart with disown
   cd /Users/ronen/Downloads/Tiktok-scraping-main\ copy\ 5
   nohup python3 api_server.py --port 8000 > api_server.log 2>&1 & disown
   
   cd synapse-ai-learning-main
   nohup npm run dev > vite.log 2>&1 & disown
   
   # Verify
   sleep 3 && lsof -nP -iTCP:8000,5001 -sTCP:LISTEN
   ```

## Configuration Files Verified

### vite.config.ts
```typescript
server: {
  port: 5001,
  strictPort: true,  // Fail if port is busy
  host: '0.0.0.0',   // Listen on all interfaces
}
```

### .env
```
VITE_API_BASE=http://localhost:8000
```

### src/lib/api.ts
```typescript
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
```

## Why This Happens "Every Time"

1. **Background process handling in zsh:**
   - Jobs started with `&` are tracked by the shell
   - When shell exits, it sends SIGHUP to background jobs
   - Without `disown`, jobs receive the signal and terminate

2. **Interactive terminal sessions:**
   - Starting services in terminals that get closed
   - Interrupting startup scripts with Ctrl+C
   - Shell session timeouts

3. **Port conflicts:**
   - Previous crashed instances holding onto ports
   - Need to explicitly kill before restart

## Prevention Checklist

- [ ] Always use `disown` after background process
- [ ] Wait 2-3 seconds after killing processes before restart
- [ ] Check logs immediately after start
- [ ] Verify ports are listening before declaring success
- [ ] Test actual HTTP response, not just port status
- [ ] Use `screen` or `tmux` for long-running development sessions

## Alternative: Production Setup

For a more stable production-like setup, consider:

1. **PM2 for Node.js:**
   ```bash
   npm install -g pm2
   pm2 start npm --name "vite-frontend" -- run dev
   pm2 start python3 --name "api-backend" -- api_server.py --port 8000
   pm2 save
   ```

2. **Docker Compose:**
   - Isolates services
   - Automatic restart policies
   - Better resource management

## Current Status (October 23, 2025)

✅ Both services running with `disown`:
- Backend: PID 31495 on port 8000
- Frontend: PID 31780 on port 5001

✅ Backend API verified working
✅ Processes detached and will survive shell exit

## Testing the Fix

1. Open http://localhost:5001 in browser
2. Should see the Synapse interface (not blank page)
3. Try refreshing multiple times
4. Check browser console for errors
5. Navigate to different pages (Search, Library, Ingest)
6. Start an ingestion and verify real-time progress updates

If still blank:
- Clear browser cache (Cmd+Shift+R on Mac)
- Check browser console for CORS errors
- Verify API_BASE environment variable is set correctly
- Check if content blocker is interfering
