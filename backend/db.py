"""
SQLite persistence layer for jobs.
Replaces the in-memory dict in job_manager.py.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = Path(__file__).parent / "jobs.db"


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent read/write
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id        TEXT PRIMARY KEY,
                status        TEXT NOT NULL,
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL,
                talk_type     TEXT,
                audience_type TEXT,
                score_value   INTEGER,
                score_label   TEXT,
                duration_sec  REAL,
                audio_path    TEXT,
                input_data    TEXT,
                result        TEXT,
                failure       TEXT
            )
        """)
        conn.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    for key in ("input_data", "result", "failure"):
        raw = d.get(key)
        d[key] = json.loads(raw) if raw else None
    for key in ("created_at", "updated_at"):
        raw = d.get(key)
        if raw:
            d[key] = datetime.fromisoformat(raw)
    return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_job(job_id: str, input_data: Dict[str, Any], audio_path: Optional[str] = None) -> None:
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs
                (job_id, status, created_at, updated_at,
                 talk_type, audience_type, audio_path, input_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                "queued",
                now,
                now,
                input_data.get("talk_type"),
                input_data.get("audience_type"),
                audio_path,
                json.dumps(input_data),
            ),
        )
        conn.commit()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    finally:
        conn.close()
    return _row_to_dict(row) if row else None


def update_job_status(job_id: str, status: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
            (status, _now(), job_id),
        )
        conn.commit()


def update_job_result(job_id: str, result: Dict[str, Any]) -> None:
    overall = result.get("overall_score", {})
    duration = result.get("input", {}).get("duration_sec")
    with _connect() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status      = 'done',
                updated_at  = ?,
                score_value = ?,
                score_label = ?,
                duration_sec = ?,
                result      = ?
            WHERE job_id = ?
            """,
            (
                _now(),
                overall.get("score_0_100"),
                overall.get("label"),
                duration,
                json.dumps(result),
                job_id,
            ),
        )
        conn.commit()


def update_job_failure(job_id: str, failure: Dict[str, Any]) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status    = 'failed',
                updated_at = ?,
                failure   = ?
            WHERE job_id = ?
            """,
            (_now(), json.dumps(failure), job_id),
        )
        conn.commit()


def set_audio_path(job_id: str, audio_path: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE jobs SET audio_path = ? WHERE job_id = ?",
            (audio_path, job_id),
        )
        conn.commit()


def delete_job(job_id: str) -> Optional[str]:
    """Delete a job row; return audio_path (if any) for caller to clean up."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT audio_path FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
        if row is None:
            return None
        audio_path = row["audio_path"]
        conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        conn.commit()
    finally:
        conn.close()
    return audio_path  # may be None if no file was stored


def list_jobs(limit: int = 50, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT job_id, status, created_at, updated_at,
                   talk_type, audience_type,
                   score_value, score_label, duration_sec
            FROM jobs
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    finally:
        conn.close()

    jobs = []
    for row in rows:
        d = dict(row)
        for key in ("created_at", "updated_at"):
            if d.get(key):
                d[key] = datetime.fromisoformat(d[key])
        jobs.append(d)
    return jobs, total
