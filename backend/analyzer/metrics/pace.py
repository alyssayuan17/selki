"""
analyzer/metrics/pace.py

Implements the "pace" metric:
- Compute WPM for the whole talk
- Compute WPM in sliding windows (e.g., 30s segments)
- Use heuristics (placeholder for a future regressor)
- Output:
  {
    "score_0_100": ...,
    "label": "...",
    "confidence": ...,
    "abstained": False,
    "details": {...},
    "feedback": [...]
  }
"""

from __future__ import annotations
from typing import List, Dict, Any
import math


# ----------------------------------------------------
# Helper: compute words per minute
# ----------------------------------------------------
def compute_wpm(words: List[Dict[str, Any]], duration_sec: float) -> float:
    if duration_sec <= 0:
        return 0.0
    num_words = len(words)
    minutes = duration_sec / 60.0
    return num_words / minutes if minutes > 0 else 0.0


# ----------------------------------------------------
# Helper: compute segmented WPM (e.g., 30-second chunks)
# ----------------------------------------------------
def compute_segment_wpm(words: List[Dict[str, Any]], segment_length: float = 30.0):
    if not words:
        return []

    segments = []
    max_time = max(w.get("end", 0.0) for w in words)

    # Divide time into segments of (segment_length)
    t = 0.0
    while t < max_time:
        segment_end = t + segment_length
        segment_words = [
            w for w in words
            if t <= w.get("start", 0) < segment_end
        ]
        wpm = compute_wpm(segment_words, segment_length)
        segments.append({
            "start_sec": t,
            "end_sec": segment_end,
            "wpm": wpm,
        })
        t += segment_length

    return segments


# ----------------------------------------------------
# Map WPM to label
# ----------------------------------------------------
def label_from_wpm(wpm: float) -> str:
    """
    Basic heuristic:
      <110 WPM → too_slow
      110–170  → optimal
      >170     → too_fast
    """

    if wpm < 110:
        return "too_slow"
    if wpm <= 170:
        return "optimal"
    return "too_fast"


# ----------------------------------------------------
# Convert label → score (simple)
# ----------------------------------------------------
def score_from_label(label: str) -> int:
    mapping = {
        "too_slow": 40,
        "optimal": 90,
        "too_fast": 50,
    }
    return mapping.get(label, 0)


# ----------------------------------------------------
# Main entrypoint
# ----------------------------------------------------
def compute_pace_metric(words: List[Dict[str, Any]], duration_sec: float) -> Dict[str, Any]:
    """
    Produces a metric object following your required schema.
    """

    if not words or duration_sec <= 0:
        # Cannot compute; abstain.
        return {
            "score_0_100": None,
            "label": "abstained",
            "confidence": 0.0,
            "abstained": True,
            "details": {"reason": "no_words"},
            "feedback": [],
        }

    # Whole-talk WPM
    wpm = compute_wpm(words, duration_sec)
    label = label_from_wpm(wpm)
    score = score_from_label(label)

    # Per-segment WPM (30s window)
    seg_stats = compute_segment_wpm(words, segment_length=30.0)

    # Confidence = heuristic; later replace with model calibration
    confidence = 0.75

    # Feedback example
    feedback = []
    if label == "too_fast":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": min(duration_sec, 30.0),
            "message": "You are speaking too fast. Try inserting 400–700 ms pauses after key points.",
            "tip_type": "pace",
        })
    if label == "too_slow":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": min(duration_sec, 30.0),
            "message": "Your speaking pace is slow. Try increasing energy or reducing pauses.",
            "tip_type": "pace",
        })

    return {
        "score_0_100": score,
        "label": label,
        "confidence": confidence,
        "abstained": False,
        "details": {
            "average_wpm": wpm,
            "optimal_range_wpm": [110, 170],
            "segment_stats": seg_stats,
        },
        "feedback": feedback,
    }
