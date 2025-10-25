# Hermes Phase 0
"""
Worker tests for Hermes Phase 0
"""

import pytest
from worker import JobKind
from worker.main import handle_generate_plan, process_job, worker_loop_tick


class TestGeneratePlanHandler:  # Hermes Phase 0
    """Test GENERATE_PLAN job handler"""
    
    @pytest.mark.asyncio
    async def test_generate_plan_stub(self):  # Hermes Phase 0
        """Handler should execute without errors and return success"""
        job_data = {
            "plan_id": "test-plan-123",
            "user_id": "user-456",
            "handle": "testcreator",
            "goal": "GROWTH"
        }
        
        result = await handle_generate_plan(job_data)
        
        assert result["status"] == "completed"
        assert "message" in result
        assert result["plan_id"] == "test-plan-123"
    
    @pytest.mark.asyncio
    async def test_process_job_routes_to_handler(self):  # Hermes Phase 0
        """process_job should route to correct handler"""
        job_data = {
            "plan_id": "test-789",
            "user_id": "user-123"
        }
        
        result = await process_job(JobKind.GENERATE_PLAN, job_data)
        
        assert result["status"] == "completed"
        assert result["plan_id"] == "test-789"
    
    @pytest.mark.asyncio
    async def test_process_job_unknown_kind(self):  # Hermes Phase 0
        """process_job should raise for unknown job kind"""
        # Create a fake job kind that doesn't exist
        with pytest.raises(ValueError, match="No handler registered"):
            await process_job("UNKNOWN_JOB", {})


class TestWorkerLoop:  # Hermes Phase 0
    """Test worker loop"""
    
    @pytest.mark.asyncio
    async def test_worker_loop_tick_stub(self):  # Hermes Phase 0
        """Worker loop tick should run without errors (stub)"""
        # Phase 0: Just verify it doesn't crash
        await worker_loop_tick()
        # No assertion needed - just shouldn't raise


if __name__ == "__main__":  # Hermes Phase 0
    pytest.main([__file__, "-v"])
