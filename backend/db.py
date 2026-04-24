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

import os
_DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent / "data"))
_DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = _DATA_DIR / "jobs.db"


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
            CREATE TABLE IF NOT EXISTS users (
                user_id    TEXT PRIMARY KEY,
                username   TEXT UNIQUE NOT NULL,
                email      TEXT UNIQUE NOT NULL,
                pw_hash    TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
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
                failure       TEXT,
                user_id       TEXT,
                saved         INTEGER DEFAULT 0
            )
        """)
        # Migrate: add columns that may not exist in older DB schemas
        for col, typedef in [
            ("score_value", "INTEGER"),
            ("score_label", "TEXT"),
            ("duration_sec", "REAL"),
            ("audio_path",   "TEXT"),
            ("input_data",   "TEXT"),
            ("result",       "TEXT"),
            ("failure",      "TEXT"),
            ("user_id",      "TEXT"),
            ("saved",        "INTEGER DEFAULT 0"),
        ]:
            try:
                conn.execute(f"ALTER TABLE jobs ADD COLUMN {col} {typedef}")
            except Exception:
                pass  # column already exists

        # Mark any jobs left in queued/processing as failed — they were
        # interrupted by a restart and will never complete.
        conn.execute(
            """
            UPDATE jobs
            SET status    = 'failed',
                updated_at = ?,
                failure   = ?
            WHERE status IN ('queued', 'processing')
            """,
            (
                _now(),
                json.dumps({
                    "code": "interrupted",
                    "message": "Job was interrupted by a server restart.",
                    "details": {},
                }),
            ),
        )
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


def list_saved_jobs(user_id: str, limit: int = 50, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT job_id, status, created_at, updated_at,
                   talk_type, audience_type,
                   score_value, score_label, duration_sec, saved
            FROM jobs
            WHERE user_id = ? AND saved = 1 AND status = 'done'
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE user_id = ? AND saved = 1 AND status = 'done'",
            (user_id,),
        ).fetchone()[0]
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


def save_job(job_id: str, user_id: str) -> bool:
    with _connect() as conn:
        conn.execute(
            "UPDATE jobs SET saved = 1, user_id = ?, updated_at = ? WHERE job_id = ?",
            (user_id, _now(), job_id),
        )
        conn.commit()
    return True


def unsave_job(job_id: str, user_id: str) -> bool:
    with _connect() as conn:
        conn.execute(
            "UPDATE jobs SET saved = 0, updated_at = ? WHERE job_id = ? AND user_id = ?",
            (_now(), job_id, user_id),
        )
        conn.commit()
    return True


def get_job_save_status(job_id: str) -> dict:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT user_id, saved FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {"saved": False, "user_id": None}
    return {"saved": bool(row["saved"]), "user_id": row["user_id"]}


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

import hashlib, os as _os

def _hash_password(password: str) -> str:
    salt = _os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
        return new_key.hex() == key_hex
    except Exception:
        return False


def create_user(username: str, email: str, password: str) -> Optional[Dict[str, Any]]:
    import uuid as _uuid
    user_id = str(_uuid.uuid4())
    now = _now()
    pw_hash = _hash_password(password)
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users (user_id, username, email, pw_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, username.strip(), email.strip().lower(), pw_hash, now),
            )
            conn.commit()
        return {"user_id": user_id, "username": username, "email": email}
    except sqlite3.IntegrityError:
        return None  # username or email already taken


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_email(email)
    if not user:
        return None
    if not _verify_password(password, user["pw_hash"]):
        return None
    return {"user_id": user["user_id"], "username": user["username"], "email": user["email"]}


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
