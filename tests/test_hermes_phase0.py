# Hermes Phase 0
"""
Backend tests for Hermes Phase 0 API routes
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

# Import the app
from api_server import app

client = TestClient(app)


class TestHermesHealth:  # Hermes Phase 0
    """Test health endpoint"""
    
    def test_health_no_auth_required(self):  # Hermes Phase 0
        """Health check should work without authentication"""
        response = client.get("/api/hermes/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data
    
    def test_health_returns_version(self):  # Hermes Phase 0
        """Health check should return version info"""
        response = client.get("/api/hermes/health")
        data = response.json()
        assert data["version"] == "0.1.0"


class TestHermesPlanSubmission:  # Hermes Phase 0
    """Test plan submission endpoint"""
    
    def test_plan_requires_auth(self):  # Hermes Phase 0
        """Plan submission should require authentication"""
        response = client.post(
            "/api/hermes/plan",
            json={"handle": "testuser", "goal": "GROWTH"}
        )
        assert response.status_code == 403  # No bearer token
    
    def test_plan_with_handle(self):  # Hermes Phase 0
        """Should accept plan request with handle"""
        response = client.post(
            "/api/hermes/plan",
            json={"handle": "testuser", "goal": "GROWTH"},
            headers={"Authorization": "Bearer stub_token"}
        )
        assert response.status_code == 202
        
        data = response.json()
        assert "plan_id" in data
        assert data["status"] == "queued"
    
    def test_plan_with_links(self):  # Hermes Phase 0
        """Should accept plan request with links"""
        response = client.post(
            "/api/hermes/plan",
            json={
                "links": ["https://example.com/video1", "https://example.com/video2"],
                "goal": "LEADS"
            },
            headers={"Authorization": "Bearer stub_token"}
        )
        assert response.status_code == 202
        
        data = response.json()
        assert "plan_id" in data
        assert data["status"] == "queued"
    
    def test_plan_requires_handle_or_links(self):  # Hermes Phase 0
        """Should reject plan request without handle or links"""
        response = client.post(
            "/api/hermes/plan",
            json={"goal": "SALES"},
            headers={"Authorization": "Bearer stub_token"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_plan_validates_goal(self):  # Hermes Phase 0
        """Should validate goal enum"""
        response = client.post(
            "/api/hermes/plan",
            json={"handle": "testuser", "goal": "INVALID_GOAL"},
            headers={"Authorization": "Bearer stub_token"}
        )
        assert response.status_code == 422


class TestHermesPlanRetrieval:  # Hermes Phase 0
    """Test plan retrieval endpoint"""
    
    def test_get_plan_requires_auth(self):  # Hermes Phase 0
        """Plan retrieval should require authentication"""
        plan_id = str(uuid4())
        response = client.get(f"/api/hermes/plans/{plan_id}")
        assert response.status_code == 403
    
    def test_get_plan_returns_stub(self):  # Hermes Phase 0
        """Should return stub plan envelope"""
        plan_id = str(uuid4())
        response = client.get(
            f"/api/hermes/plans/{plan_id}",
            headers={"Authorization": "Bearer stub_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["plan_id"] == plan_id
        assert data["status"] in ["queued", "running", "ready", "failed"]
        assert "goal" in data
        assert "meta" in data
        assert data["meta"]["source_type"] in ["handle", "links"]


class TestHermesInsight:  # Hermes Phase 0
    """Test insight generation endpoint"""
    
    def test_insight_requires_auth(self):  # Hermes Phase 0
        """Insight generation should require authentication"""
        response = client.post(
            "/api/hermes/insight",
            json={"url": "https://example.com/video"}
        )
        assert response.status_code == 403
    
    def test_insight_returns_stub(self):  # Hermes Phase 0
        """Should return stub insight data"""
        response = client.post(
            "/api/hermes/insight",
            json={"url": "https://example.com/video"},
            headers={"Authorization": "Bearer stub_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "pattern" in data
        assert "why" in data
        assert "improvement" in data
        assert "receipts" in data
        assert isinstance(data["receipts"], list)
    
    def test_insight_validates_url(self):  # Hermes Phase 0
        """Should validate URL format"""
        response = client.post(
            "/api/hermes/insight",
            json={"url": "not-a-valid-url"},
            headers={"Authorization": "Bearer stub_token"}
        )
        assert response.status_code == 422


class TestHermesFeatureFlag:  # Hermes Phase 0
    """Test feature flag behavior"""
    
    def test_hermes_enabled_by_default(self):  # Hermes Phase 0
        """Hermes routes should be accessible when enabled"""
        response = client.get("/api/hermes/health")
        assert response.status_code == 200


if __name__ == "__main__":  # Hermes Phase 0
    pytest.main([__file__, "-v"])
