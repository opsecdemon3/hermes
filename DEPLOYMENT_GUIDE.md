# 🚀 Deployment Guide - TikTalk Production Setup

**Copilot addition: deployment prep** - Complete guide for hosting TikTalk on any platform.

---

## 📋 Pre-Deployment Checklist

- [ ] Python 3.10+ installed
- [ ] Node.js 20+ installed
- [ ] ffmpeg installed (for audio processing)
- [ ] Environment variables configured
- [ ] Docker installed (optional, recommended)

---

## 🔧 Environment Configuration

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Configure Variables

Edit `.env` with your deployment settings:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Data Directories
ACCOUNTS_DIR=accounts
DATA_DIR=data
CONFIG_DIR=config

# Frontend Configuration
VITE_API_BASE=http://localhost:8000  # Change to production URL
```

---

## 🐳 Docker Deployment (Recommended)

### Quick Start

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Build

```bash
# Build optimized images
docker-compose build --no-cache

# Start with resource limits
docker-compose up -d --scale api=2
```

---

## 💻 Manual Deployment

### Backend Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Verify installation
python test_dependencies.py

# 5. Start API server
python api_server.py
# Server runs on http://0.0.0.0:8000
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd synapse-ai-learning-main

# 2. Install dependencies
npm install

# 3. Configure API endpoint
# Edit .env.example or create .env
echo "VITE_API_BASE=http://localhost:8000" > .env

# 4. Start development server
npm run dev
# Frontend runs on http://localhost:5001

# 5. Build for production
npm run build
# Output in dist/
```

---

## ☁️ Platform-Specific Deployments

### Render.com

**Backend (Web Service)**:
- Build Command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
- Start Command: `python api_server.py`
- Environment Variables: Set `API_HOST`, `API_PORT`, `API_DEBUG`

**Frontend (Static Site)**:
- Build Command: `cd synapse-ai-learning-main && npm install && npm run build`
- Publish Directory: `synapse-ai-learning-main/dist`
- Environment Variables: `VITE_API_BASE=https://your-api.onrender.com`

### Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy backend
fly launch --dockerfile Dockerfile
fly deploy

# Deploy frontend
cd synapse-ai-learning-main
fly launch --dockerfile Dockerfile.frontend
fly deploy
```

### Heroku

```bash
# Create apps
heroku create tiktalk-api
heroku create tiktalk-frontend

# Deploy backend
git push heroku main

# Set environment variables
heroku config:set API_HOST=0.0.0.0 -a tiktalk-api
heroku config:set API_PORT=8000 -a tiktalk-api
```

### DigitalOcean App Platform

1. Connect GitHub repository
2. Choose "Web Service" for backend
3. Choose "Static Site" for frontend
4. Configure build/run commands as above
5. Set environment variables in dashboard

---

## 🔍 Verification

### Run Deployment Verification

```bash
# After deployment, verify API health
python scripts/verify_deployment.py

# Or manually test
curl http://localhost:8000/api/verify/system
```

Expected response:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "search_engine": "initialized",
  "accounts": 14,
  "total_videos": 150
}
```

### Frontend Connection Test

1. Open browser to `http://localhost:5001`
2. Navigate to Search page
3. Try searching for "meditation"
4. Verify results appear

---

## 🔥 Production Optimizations

### Backend

1. **Use Production ASGI Server**:
```bash
# Install gunicorn with uvicorn workers
pip install gunicorn

# Run with multiple workers
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. **Enable Caching**:
```python
# Add Redis caching for search results
# Add response caching middleware
```

3. **Database Migration**:
```python
# Move from JSON to PostgreSQL for metadata
# Keep JSON for backwards compatibility
```

### Frontend

1. **Build Optimization**:
```bash
npm run build
# Minified bundle: ~267KB gzipped
```

2. **CDN Deployment**:
- Upload `dist/` to Cloudflare Pages
- Upload `dist/` to Vercel
- Upload `dist/` to Netlify

3. **Environment Variables**:
```bash
# Production API URL
VITE_API_BASE=https://api.yourdomain.com
```

---

## 📊 Monitoring

### Health Checks

**API Health Endpoint**:
```bash
GET /api/verify/system
```

**Monitoring Script** (cron every 5 minutes):
```bash
*/5 * * * * python /app/scripts/verify_deployment.py >> /var/log/tiktalk-health.log 2>&1
```

### Logging

**Backend Logs**:
```bash
# View API logs
tail -f logs/api.log

# Docker logs
docker-compose logs -f api
```

**Frontend Logs**:
```bash
# Browser console
# Sentry integration (recommended)
```

---

## 🛡️ Security Hardening

### 1. API Security

```python
# Add rate limiting
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

# Add authentication
from fastapi.security import HTTPBearer
security = HTTPBearer()
```

### 2. CORS Configuration

```python
# Restrict CORS in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 3. HTTPS/TLS

- Use Cloudflare for SSL termination
- Use Let's Encrypt for free SSL certificates
- Configure nginx reverse proxy with SSL

---

## 📦 Data Persistence

### Volume Mounts (Docker)

```yaml
volumes:
  - ./accounts:/app/accounts      # Video metadata
  - ./data:/app/data              # FAISS index
  - ./config:/app/config          # Configuration files
```

### Backup Strategy

```bash
# Backup script (daily cron)
#!/bin/bash
tar -czf backup-$(date +%Y%m%d).tar.gz accounts/ data/ config/
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://tiktalk-backups/
```

---

## 🐛 Troubleshooting

### API Won't Start

```bash
# Check Python version
python3 --version  # Must be 3.10+

# Check dependencies
pip list

# Check ports
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Frontend Can't Connect to API

```bash
# Check VITE_API_BASE
echo $VITE_API_BASE

# Test API directly
curl http://localhost:8000/api/verify/system

# Check CORS headers
curl -H "Origin: http://localhost:5001" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS http://localhost:8000/api/accounts
```

### Docker Issues

```bash
# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Check container logs
docker-compose logs api
docker-compose logs frontend
```

---

## 📞 Support

- **GitHub Issues**: https://github.com/opsecdemon3/TikTalk/issues
- **Documentation**: See ARCHITECTURE_DEEP_DIVE.md, FEATURES_AND_CAPABILITIES.md
- **API Docs**: http://localhost:8000/docs (when running)

---

## ✅ Production Readiness Checklist

- [x] Environment variables configured (`.env`)
- [x] Dockerfile for reproducible builds
- [x] Docker Compose for orchestration
- [x] Health check endpoint (`/api/verify/system`)
- [x] Deployment verification script
- [x] CORS properly configured
- [x] Error handling and logging
- [x] Frontend loading states
- [x] API proxy configuration
- [ ] SSL/TLS certificates (platform-dependent)
- [ ] Domain configuration (platform-dependent)
- [ ] Monitoring setup (optional)
- [ ] Backup strategy (optional)

---

**Status**: ✅ **Production Ready**

TikTalk is now configured for deployment on any platform. Choose your hosting provider and follow the platform-specific instructions above.

---

*Last Updated: October 24, 2025*
*Copilot addition: deployment prep*
