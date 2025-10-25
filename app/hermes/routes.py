# Hermes Phase 0
"""
Hermes API routes (Phase 0: stubs with contracts)
"""

from datetime import datetime
from typing import Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.hermes.schemas import (
    HealthResponse,
    PlanRequest,
    PlanSubmitResponse,
    PlanEnvelope,
    PlanMeta,
    InsightRequest,
    InsightResponse,
    Goal
)
from app.hermes.service import HermesService
from app.hermes.errors import PlanNotFoundError

# Hermes Phase 0
router = APIRouter(prefix="/api/hermes", tags=["hermes"])
security = HTTPBearer()


# Hermes Phase 0 - Simple auth dependency (stub - replace with real JWT validation)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract user ID from JWT token
    Phase 0: Stub implementation - accepts any bearer token
    TODO: Replace with real JWT validation in Phase 1
    """
    # Hermes Phase 0: Accept any token, return stub user ID
    # In production, this should validate JWT and extract user_id
    return "stub_user_001"


@router.get("/health", response_model=HealthResponse)  # Hermes Phase 0
async def health_check() -> HealthResponse:
    """
    Health check endpoint (no auth required)
    
    Returns:
        Health status, version, and timestamp
    """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.utcnow()
    )


@router.post(
    "/plan",
    response_model=PlanSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED
)  # Hermes Phase 0
async def submit_plan(
    request: PlanRequest,
    user_id: str = Depends(get_current_user)
) -> PlanSubmitResponse:
    """
    Submit a plan generation request
    
    Args:
        request: Plan request (handle or links + goal)
        user_id: Authenticated user ID
    
    Returns:
        202 Accepted with plan_id and queued status
    
    Phase 0: Returns stub plan_id without queuing job
    """
    # Hermes Phase 0: Generate stub plan ID
    plan_id = uuid4()
    
    # TODO Phase 1: Queue GENERATE_PLAN job with plan_id
    # TODO Phase 1: Store plan metadata in database
    
    return PlanSubmitResponse(
        plan_id=plan_id,
        status="queued"
    )


@router.get("/plans/{plan_id}", response_model=PlanEnvelope)  # Hermes Phase 0
async def get_plan(
    plan_id: UUID,
    user_id: str = Depends(get_current_user)
) -> PlanEnvelope:
    """
    Retrieve a plan by ID
    
    Args:
        plan_id: Plan UUID
        user_id: Authenticated user ID
    
    Returns:
        Plan envelope with status and items (if ready)
    
    Phase 0: Returns stub envelope with queued status
    """
    # Hermes Phase 0: Return stub plan envelope
    # TODO Phase 1: Query database for real plan data
    
    return PlanEnvelope(
        plan_id=plan_id,
        status="queued",
        goal=Goal.growth,
        summary=None,
        items=None,
        pdf_signed_url=None,
        meta=PlanMeta(
            source_type="handle",
            inputs={"stub": True},
            created_at=datetime.utcnow()
        )
    )


@router.post("/insight", response_model=InsightResponse)  # Hermes Phase 0
async def generate_insight(
    request: InsightRequest,
    user_id: str = Depends(get_current_user)
) -> InsightResponse:
    """
    Generate content insight for a URL
    
    Args:
        request: Insight request with URL
        user_id: Authenticated user ID
    
    Returns:
        Pattern, reasoning, improvement suggestion, and receipts
    
    Phase 0: Returns static stub data
    """
    # Hermes Phase 0: Return stub insight
    # TODO Phase 1: Implement real pattern analysis
    
    return InsightResponse(
        pattern="Hook-Story-CTA structure",
        why="This pattern captures attention in first 3 seconds and drives action",
        improvement="Consider adding a visual hook in the first frame",
        receipts=[]
    )
