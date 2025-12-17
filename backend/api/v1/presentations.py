"""
FastAPI endpoints for presentation analysis.

Endpoints:
- POST   /api/v1/presentations          - Submit audio for analysis
- GET    /api/v1/presentations/{job_id} - Get analysis status
- GET    /api/v1/presentations/{job_id}/full - Get full results
- GET    /api/v1/presentations/{job_id}/transcript - Get transcript
- DELETE /api/v1/presentations/{job_id} - Delete job
"""

from __future__ import annotations
import asyncio
from typing import Union
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from datetime import datetime, timezone

from api.v1.schemas import (
    PresentationCreateRequest,
    PresentationCreateResponse,
    PresentationStatusProcessing,
    PresentationStatusDone,
    PresentationStatusFailed,
    PresentationFullResponse,
    PresentationTranscriptResponse,
    PresentationTranscriptProcessing,
    InputBlock,
    QualityFlags,
    OverallScore,
    MetricResult,
    TimelineEvent,
    ModelMetadata,
    TranscriptBlock,
    TranscriptDetailed,
    TranscriptSegment,
    TranscriptToken,
    MetricFeedback,
)
from jobs.job_manager import JobManager

router = APIRouter(prefix="/api/v1", tags=["presentations"])


# ============================================================================
# POST /api/v1/presentations
# ============================================================================

@router.post(
    "/presentations",
    response_model=PresentationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_presentation(
    request: PresentationCreateRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit audio for presentation analysis.

    Creates a job and starts processing in the background.

    Returns:
        201 Created with job_id and status
    """
    # Create job
    input_dict = request.model_dump()
    job_id = JobManager.create_job(input_dict)

    # Start processing in background
    background_tasks.add_task(JobManager.process_job, job_id)

    # Return 201 response
    job = JobManager.get_job(job_id)
    return PresentationCreateResponse(
        job_id=job_id,
        status="queued",
        created_at=job["created_at"],
        input=InputBlock(**input_dict),
    )


# ============================================================================
# GET /api/v1/presentations/{job_id}
# ============================================================================

@router.get(
    "/presentations/{job_id}",
    response_model=Union[
        PresentationStatusProcessing,
        PresentationStatusDone,
        PresentationStatusFailed,
    ],
)
async def get_presentation_status(job_id: str):
    """
    Get presentation analysis status.

    Returns different response schemas based on job status:
    - processing: job_id, status, created_at, updated_at
    - done: includes input, quality_flags, overall_score, available_metrics
    - failed: includes failure info

    Raises:
        404: Job not found
    """
    job = JobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    status_value = job["status"]

    # Processing
    if status_value in ("queued", "processing"):
        return PresentationStatusProcessing(
            job_id=job_id,
            status=status_value,
            created_at=job["created_at"],
            updated_at=job["updated_at"],
        )

    # Failed
    if status_value == "failed":
        return PresentationStatusFailed(
            job_id=job_id,
            status="failed",
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            failure=job["failure"],
        )

    # Done
    if status_value == "done":
        result = job["result"]
        return PresentationStatusDone(
            job_id=job_id,
            status="done",
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            input=InputBlock(**result["input"]),
            quality_flags=QualityFlags(**result["quality_flags"]),
            overall_score=OverallScore(**result["overall_score"]),
            available_metrics=list(result["metrics"].keys()),
        )

    # Unknown status (shouldn't happen)
    raise HTTPException(status_code=500, detail=f"Unknown job status: {status_value}")


# ============================================================================
# GET /api/v1/presentations/{job_id}/full
# ============================================================================

@router.get(
    "/presentations/{job_id}/full",
    response_model=PresentationFullResponse,
)
async def get_presentation_full(job_id: str):
    """
    Get full presentation analysis results.

    Includes all metrics, timeline, and transcript.

    Raises:
        404: Job not found
        409: Job not yet completed (still processing or failed)
    """
    job = JobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=f"Job {job_id} is {job['status']}, not done yet",
        )

    result = job["result"]

    # Convert metrics to MetricResult objects
    metrics = {}
    for metric_name, metric_data in result["metrics"].items():
        # Convert feedback items
        feedback = [
            MetricFeedback(**fb) for fb in metric_data.get("feedback", [])
        ]

        metrics[metric_name] = MetricResult(
            score_0_100=metric_data.get("score_0_100"),
            label=metric_data["label"],
            confidence=metric_data["confidence"],
            abstained=metric_data.get("abstained", False),
            details=metric_data.get("details", {}),
            feedback=feedback,
        )

    # Convert timeline
    timeline = [TimelineEvent(**event) for event in result.get("timeline", [])]

    return PresentationFullResponse(
        job_id=job_id,
        status="done",
        input=InputBlock(**result["input"]),
        quality_flags=QualityFlags(**result["quality_flags"]),
        overall_score=OverallScore(**result["overall_score"]),
        metrics=metrics,
        timeline=timeline,
        model_metadata=ModelMetadata(**result["model_metadata"]),
        transcript=TranscriptBlock(**result["transcript"]),
    )


# ============================================================================
# GET /api/v1/presentations/{job_id}/transcript
# ============================================================================

@router.get(
    "/presentations/{job_id}/transcript",
    response_model=Union[PresentationTranscriptResponse, PresentationTranscriptProcessing],
)
async def get_presentation_transcript(job_id: str):
    """
    Get presentation transcript.

    Returns detailed transcript with segments and tokens when done,
    or processing status if not yet complete.

    Raises:
        404: Job not found
    """
    job = JobManager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Still processing
    if job["status"] in ("queued", "processing"):
        return PresentationTranscriptProcessing(
            job_id=job_id,
            status=job["status"],
        )

    # Failed
    if job["status"] == "failed":
        raise HTTPException(
            status_code=409,
            detail=f"Job {job_id} failed: {job['failure']['message']}",
        )

    # Done - return detailed transcript
    result = job["result"]

    # Get transcript from result
    # Note: We'll need to enhance run_pipeline.py to include segments/tokens
    # For now, return basic transcript
    transcript_data = result.get("transcript", {})

    # TODO: Add segments and tokens to run_pipeline.py output
    # For now, return minimal transcript
    detailed_transcript = TranscriptDetailed(
        full_text=transcript_data.get("full_text", ""),
        language=transcript_data.get("language", "en"),
        segments=[],  # TODO: Add from audio_to_json
        tokens=[],    # TODO: Add from audio_to_json
    )

    return PresentationTranscriptResponse(
        job_id=job_id,
        status="done",
        transcript=detailed_transcript,
    )


# ============================================================================
# DELETE /api/v1/presentations/{job_id}
# ============================================================================

@router.delete(
    "/presentations/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_presentation(job_id: str):
    """
    Delete a presentation job.

    Returns:
        204 No Content

    Raises:
        404: Job not found
    """
    deleted = JobManager.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return None  # 204 No Content
