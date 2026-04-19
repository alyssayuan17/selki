"""
Job manager backed by SQLite persistence.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests as http_requests

import db
from analyzer.run_pipeline import run_full_analysis

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


class JobManager:

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    def create_job(input_data: Dict[str, Any]) -> str:
        job_id = f"pres_{uuid.uuid4().hex[:10]}"

        # For file:// uploads, store the local path so we can clean up on delete
        audio_url = input_data.get("audio_url", "")
        audio_path: Optional[str] = None
        if audio_url.startswith("file://"):
            audio_path = audio_url.replace("file://", "")

        db.create_job(job_id, input_data, audio_path=audio_path)
        logger.info(f"Created job {job_id}, status=queued")
        return job_id

    # ------------------------------------------------------------------
    # Process (background task)
    # ------------------------------------------------------------------

    @staticmethod
    async def process_job(job_id: str) -> None:
        job = db.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found in db")
            return

        db.update_job_status(job_id, "processing")
        logger.info(f"Job {job_id} started processing")

        try:
            input_dict = job["input_data"]
            audio_url: str = input_dict["audio_url"]

            if audio_url.startswith("file://"):
                audio_path = Path(audio_url.replace("file://", ""))
            else:
                # Download remote audio to uploads directory
                audio_path = await asyncio.to_thread(
                    _download_audio, audio_url, job_id
                )
                db.set_audio_path(job_id, str(audio_path))

            result = await asyncio.to_thread(
                run_full_analysis,
                job_id=job_id,
                audio_path=audio_path,
                raw_input_payload=input_dict,
            )

            db.update_job_result(job_id, result)
            logger.info(f"Job {job_id} completed successfully")

            # Clean up upload file after successful analysis
            if audio_url.startswith("file://"):
                _delete_upload(audio_url.replace("file://", ""))

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            db.update_job_failure(job_id, {
                "code": "analysis_error",
                "message": str(e),
                "details": {"error_type": type(e).__name__},
            })

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        row = db.get_job(job_id)
        if not row:
            return None
        # Map db column names → legacy dict shape used by presentations.py
        return {
            "job_id": row["job_id"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "input": row.get("input_data") or {},
            "result": row.get("result"),
            "failure": row.get("failure"),
        }

    @staticmethod
    def list_jobs(limit: int = 50, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        return db.list_jobs(limit=limit, offset=offset)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    def delete_job(job_id: str) -> bool:
        audio_path = db.delete_job(job_id)
        if audio_path is None:
            return False  # job not found

        # Clean up the audio file if it lives inside uploads/
        if audio_path:
            _delete_upload(audio_path)

        return True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _download_audio(audio_url: str, job_id: str) -> Path:
    """Download a remote audio URL into the uploads directory."""
    UPLOADS_DIR.mkdir(exist_ok=True)

    from urllib.parse import urlparse
    parsed = urlparse(audio_url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}:
        suffix = ".mp3"

    dest = UPLOADS_DIR / f"{job_id}{suffix}"

    try:
        response = http_requests.get(audio_url, stream=True, timeout=120)
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=65_536):
                f.write(chunk)
        logger.info(f"Downloaded audio to {dest} ({dest.stat().st_size} bytes)")
        return dest
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to download audio from {audio_url}: {e}") from e


def _delete_upload(audio_path: str) -> None:
    """Delete a file only if it's inside the uploads directory."""
    p = Path(audio_path)
    try:
        if p.exists() and p.is_file():
            # Safety: only delete files within uploads/
            p.resolve().relative_to(UPLOADS_DIR.resolve())
            p.unlink()
            logger.info(f"Deleted upload file: {p}")
    except ValueError:
        logger.warning(f"Skipping deletion of file outside uploads dir: {p}")
    except OSError as e:
        logger.warning(f"Could not delete file {p}: {e}")
