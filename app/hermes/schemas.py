# Hermes Phase 0
"""
Pydantic schemas for Hermes API
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, HttpUrl, field_validator, model_validator


class Goal(str, Enum):  # Hermes Phase 0
    """Content strategy goals"""
    growth = "GROWTH"
    leads = "LEADS"
    sales = "SALES"


class PlanRequest(BaseModel):  # Hermes Phase 0
    """Request to generate a content plan"""
    handle: Optional[str] = None
    links: List[HttpUrl] = []
    goal: Goal
    
    class Config:
        extra = "forbid"
    
    @model_validator(mode="after")  # Hermes Phase 0
    def require_handle_or_links(self):
        """Ensure at least handle or links is provided"""
        if not self.handle and not self.links:
            raise ValueError("Either 'handle' or 'links' must be provided")
        return self


class PlanMeta(BaseModel):  # Hermes Phase 0
    """Metadata about plan generation"""
    source_type: Literal["handle", "links"]
    inputs: Dict[str, Any]
    created_at: datetime


class PlanItem(BaseModel):  # Hermes Phase 0
    """Single content item in a plan"""
    day_index: int
    hook: str
    outline: List[str]
    cta: str
    length_s: int
    receipts: List[Dict[str, Any]]  # {video_id, start, end}


class PlanEnvelope(BaseModel):  # Hermes Phase 0
    """Complete plan response envelope"""
    plan_id: UUID
    status: Literal["queued", "running", "ready", "failed"]
    goal: Goal
    summary: Optional[Dict[str, Any]] = None
    items: Optional[List[PlanItem]] = None
    pdf_signed_url: Optional[HttpUrl] = None
    meta: PlanMeta


class PlanSubmitResponse(BaseModel):  # Hermes Phase 0
    """Response when submitting a plan request"""
    plan_id: UUID
    status: Literal["queued"]


class InsightRequest(BaseModel):  # Hermes Phase 0
    """Request for content insight"""
    url: HttpUrl
    
    class Config:
        extra = "forbid"


class InsightResponse(BaseModel):  # Hermes Phase 0
    """Content insight response"""
    pattern: str
    why: str
    improvement: str
    receipts: List[Dict[str, Any]]


class HealthResponse(BaseModel):  # Hermes Phase 0
    """Health check response"""
    status: Literal["ok"]
    version: str
    timestamp: datetime
