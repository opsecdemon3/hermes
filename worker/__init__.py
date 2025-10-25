# Hermes Phase 0
"""
Job types for background workers
"""

from enum import Enum


class JobKind(str, Enum):  # Hermes Phase 0
    """Types of background jobs"""
    GENERATE_PLAN = "GENERATE_PLAN"  # Hermes Phase 0
