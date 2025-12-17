"""
Simple in-memory job manager with async task execution.

For production, replace with Celery + Redis or a database-backed solution.
"""

from __future__ import annotations
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from analyzer.run_pipeline import run_full_analysis

logger = logging.getLogger(__name__)


# In-memory job storage (replace with database in production)
_JOBS: Dict[str, Dict[str, Any]] = {}


class JobManager:
    """Manages job lifecycle and execution"""

    @staticmethod
    def create_job(input_data: Dict[str, Any]) -> str:
        """
        Create a new job and return job_id.

        Args:
            input_data: Request payload from POST /api/v1/presentations

        Returns:
            job_id
        """
        job_id = f"pres_{uuid.uuid4().hex[:10]}"

        now = datetime.now(timezone.utc)

        _JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "created_at": now,
            "updated_at": now,
            "input": input_data,
            "result": None,
            "failure": None,
        }

        logger.info(f"Created job {job_id}, status=queued")
        return job_id

    @staticmethod
    async def process_job(job_id: str):
        """
        Process a job asynchronously.

        This runs the analysis pipeline and updates job status.

        Args:
            job_id: Job ID to process
        """
        if job_id not in _JOBS:
            logger.error(f"Job {job_id} not found")
            return

        job = _JOBS[job_id]

        # Update status to processing
        job["status"] = "processing"
        job["updated_at"] = datetime.now(timezone.utc)
        logger.info(f"Job {job_id} started processing")

        try:
            # Get input data
            input_dict = job["input"]

            # Extract audio URL and convert to Path
            audio_url = input_dict["audio_url"]
            # Handle file:// URLs
            if audio_url.startswith("file://"):
                audio_path = Path(audio_url.replace("file://", ""))
            else:
                # For now, assume it's a local path or we download it
                # TODO: Add support for downloading from URLs
                audio_path = Path(audio_url)

            # Run the analysis pipeline (this is the heavy computation)
            result = await asyncio.to_thread(
                run_full_analysis,
                job_id=job_id,
                audio_path=audio_path,
                raw_input_payload=input_dict,
            )

            # Update job with results
            job["status"] = "done"
            job["result"] = result
            job["updated_at"] = datetime.now(timezone.utc)
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            # Handle failure
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            job["status"] = "failed"
            job["failure"] = {
                "code": "analysis_error",
                "message": str(e),
                "details": {"error_type": type(e).__name__},
            }
            job["updated_at"] = datetime.now(timezone.utc)

    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job dict or None if not found
        """
        return _JOBS.get(job_id)

    @staticmethod
    def get_job_status(job_id: str) -> Optional[str]:
        """
        Get job status.

        Args:
            job_id: Job ID

        Returns:
            Status string ("queued", "processing", "done", "failed") or None
        """
        job = _JOBS.get(job_id)
        return job["status"] if job else None

    @staticmethod
    def delete_job(job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: Job ID

        Returns:
            True if deleted, False if not found
        """
        if job_id in _JOBS:
            del _JOBS[job_id]
            logger.info(f"Deleted job {job_id}")
            return True
        return False

    @staticmethod
    def list_jobs() -> list[str]:
        """Get list of all job IDs"""
        return list(_JOBS.keys())
