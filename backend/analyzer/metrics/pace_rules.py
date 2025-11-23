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