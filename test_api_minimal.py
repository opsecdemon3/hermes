#!/usr/bin/env python3
"""
Minimal API test to debug semantic search endpoints
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Test import
try:
    from core.semantic_search.engine import SemanticSearchEngine
    print("✅ Semantic search import successful")
    search_engine = SemanticSearchEngine()
    print("✅ Search engine initialized")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Create minimal app
app = FastAPI(title="Test API", version="1.0.0")

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    text: str
    video_id: str
    username: str
    score: float

@app.get("/")
async def root():
    return {"message": "Test API", "search_available": True}

@app.post("/api/search/semantic")
async def semantic_search(request: SearchRequest):
    """Test semantic search endpoint"""
    try:
        results = search_engine.search(request.query, request.top_k)
        return {
            "query": request.query,
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("Starting test server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
