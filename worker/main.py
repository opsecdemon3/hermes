# Hermes Phase 0
"""
Worker main loop (Phase 0: stub)
"""

import logging
from typing import Dict, Any, Callable
from worker import JobKind

logger = logging.getLogger(__name__)


# Hermes Phase 0 - Job handlers registry
JOB_HANDLERS: Dict[JobKind, Callable] = {}  # Hermes Phase 0


def register_handler(job_kind: JobKind):  # Hermes Phase 0
    """Decorator to register a job handler"""
    def decorator(func: Callable):
        JOB_HANDLERS[job_kind] = func
        return func
    return decorator


@register_handler(JobKind.GENERATE_PLAN)  # Hermes Phase 0
async def handle_generate_plan(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GENERATE_PLAN job (Phase 0: stub)
    
    Args:
        job_data: Job payload with plan_id, user_id, request data
    
    Returns:
        Result data
    
    Phase 0: No-op that logs and returns success
    """
    logger.info("Hermes Phase 0: GENERATE_PLAN stub - job_data=%s", job_data)  # Hermes Phase 0
    
    # Hermes Phase 0: Stub implementation - no actual work
    # TODO Phase 1: Implement actual plan generation logic
    #   - Fetch creator content or analyze links
    #   - Run pattern detection
    #   - Generate plan items
    #   - Store in database
    #   - Update job status
    
    return {
        "status": "completed",
        "message": "Hermes Phase 0: GENERATE_PLAN stub executed",
        "plan_id": job_data.get("plan_id")
    }


async def process_job(job_kind: JobKind, job_data: Dict[str, Any]) -> Dict[str, Any]:  # Hermes Phase 0
    """
    Process a single job
    
    Args:
        job_kind: Type of job to process
        job_data: Job payload
    
    Returns:
        Job result
    
    Raises:
        ValueError: If job_kind has no registered handler
    """
    handler = JOB_HANDLERS.get(job_kind)  # Hermes Phase 0
    if not handler:
        raise ValueError(f"No handler registered for job kind: {job_kind}")
    
    return await handler(job_data)


async def worker_loop_tick():  # Hermes Phase 0
    """
    Single tick of worker loop (Phase 0: stub)
    
    In production, this would:
    1. Poll job queue for pending jobs
    2. Mark job as running
    3. Process job with appropriate handler
    4. Mark job as done/failed
    5. Store result
    
    Phase 0: No-op for testing
    """
    logger.debug("Hermes Phase 0: worker_loop_tick stub")  # Hermes Phase 0
    pass


if __name__ == "__main__":  # Hermes Phase 0
    import asyncio
    
    # Hermes Phase 0: Simple test
    async def main():
        result = await process_job(
            JobKind.GENERATE_PLAN,
            {"plan_id": "test-123", "user_id": "user-1"}
        )
        print(f"Result: {result}")
    
    asyncio.run(main())
