# Hermes Phase 0
"""
Hermes error types and error handling
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class HermesError(Exception):  # Hermes Phase 0
    """Base exception for Hermes errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_http_exception(self) -> HTTPException:  # Hermes Phase 0
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "error": self.__class__.__name__,
                "message": self.message,
                **self.details
            }
        )


class PlanNotFoundError(HermesError):  # Hermes Phase 0
    """Raised when a plan ID doesn't exist"""
    
    def __init__(self, plan_id: str):
        super().__init__(
            message=f"Plan {plan_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"plan_id": plan_id}
        )


class InvalidInputError(HermesError):  # Hermes Phase 0
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class PlanGenerationError(HermesError):  # Hermes Phase 0
    """Raised when plan generation fails"""
    
    def __init__(self, message: str, plan_id: Optional[str] = None):
        details = {"plan_id": plan_id} if plan_id else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )
