"""
analyzer/metrics/pace.py

Rule-based "pace" metric:
- Compute words per minute (WPM)
- Compute per-segment WPM (30s windows)
- Heuristically map to:
    too_slow / optimal / too_fast
- Produce:
    score_0_100, label, confidence, details, feedback
"""

from __future__ import annotations
from typing import List, Dict, Any


# ----------------------------------------------------
# Compute WPM
# ----------------------------------------------------
def compute_wpm(words: List[Dict[str, Any]], duration_sec: float) -> float:
    if duration_sec <= 0:
        return 0.0
    num_words = len(words)
    minutes = duration_sec / 60.0
    return num_words / minutes if minutes > 0 else 0.0


# ----------------------------------------------------
# Compute segmented WPM (e.g., 30s windows)
#   - Uses actual talk duration, not fixed 30s for all segments
#   - Last segment may be shorter than segment_length
# ----------------------------------------------------
def compute_segment_wpm(
    words: List[Dict[str, Any]],
    duration_sec: float,
    segment_length: float = 30.0,
) -> List[Dict[str, Any]]:
    """
    Split [0, duration_sec] into windows of at most segment_length seconds.

    Example:
      duration_sec = 20s  -> 1 segment: [0, 20]
      duration_sec = 105s -> segments:
          [0, 30], [30, 60], [60, 90], [90, 105]  (last is 15s)
    """
    if not words or duration_sec <= 0:
        return []

    segments: List[Dict[str, Any]] = []

    t = 0.0
    while t < duration_sec:
        segment_end = min(t + segment_length, duration_sec)
        seg_duration = segment_end - t
        if seg_duration <= 0:
            break

        segment_words = [
            w for w in words
            if t <= w.get("start", 0.0) < segment_end
        ]

        # Use the actual segment duration, not a fixed 30s
        wpm = compute_wpm(segment_words, seg_duration)

        segments.append({
            "start_sec": t,
            "end_sec": segment_end,
            "wpm": wpm,
        })

        t += segment_length

    return segments


# ----------------------------------------------------
# Map WPM → label
# ----------------------------------------------------
def label_from_wpm(wpm: float) -> str:
    if wpm < 110:
        return "too_slow"
    if wpm <= 170:
        return "optimal"
    return "too_fast"


# ----------------------------------------------------
# Convert label → score
# ----------------------------------------------------
def score_from_label(label: str) -> int:
    mapping = {
        "too_slow": 40,
        "optimal": 90,
        "too_fast": 50,
    }
    return mapping.get(label, 0)


# ----------------------------------------------------
# Build feedback for an individual segment
# ----------------------------------------------------
def feedback_for_segment(seg: Dict[str, Any]) -> Dict[str, Any] | None:
    wpm = seg["wpm"]
    start = seg["start_sec"]
    end = seg["end_sec"]

    if wpm < 110:
        return {
            "start_sec": start,
            "end_sec": end,
            "message": f"In this segment (WPM={wpm:.1f}), your pace is slow. "
                       "Consider increasing energy or reducing long pauses.",
            "tip_type": "pace",
        }

    if wpm > 170:
        return {
            "start_sec": start,
            "end_sec": end,
            "message": f"In this segment (WPM={wpm:.1f}), you're speaking too fast. "
                       "Pause briefly after major points to improve clarity.",
            "tip_type": "pace",
        }

    # No feedback for optimal segments
    return None


# ----------------------------------------------------
# Main entrypoint
# ----------------------------------------------------
def compute_pace_metric(words: List[Dict[str, Any]], duration_sec: float) -> Dict[str, Any]:

    if not words or duration_sec <= 0:
        return {
            "score_0_100": None,
            "label": "abstained",
            "confidence": 0.0,
            "abstained": True,
            "details": {"reason": "no_words"},
            "feedback": [],
        }

    # ------------------------------------------------------------------
    # 1. Compute overall talk pace
    # ------------------------------------------------------------------
    wpm = compute_wpm(words, duration_sec)
    label = label_from_wpm(wpm)
    score = score_from_label(label)

    # Per-segment WPM (30-second windows)
    seg_stats = compute_segment_wpm(words, duration_sec, segment_length=30.0)

    # ------------------------------------------------------------------
    # 2. Build overall feedback
    # ------------------------------------------------------------------
    overall_feedback = []
    if label == "too_fast":
        overall_feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"Your overall pace is too fast (WPM={wpm:.1f}). "
                "Aim for the 110–170 WPM range and insert 400–700 ms pauses."
            ),
            "tip_type": "pace",
        })

    elif label == "too_slow":
        overall_feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"Your overall pace is slow (WPM={wpm:.1f}). "
                "Try increasing vocal energy and reducing long pauses."
            ),
            "tip_type": "pace",
        })

    else:  # optimal
        overall_feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"Your speaking pace is in the optimal range (WPM={wpm:.1f}). "
                "Great job maintaining clarity and rhythm."
            ),
            "tip_type": "pace",
        })

    # ------------------------------------------------------------------
    # 3. Build per-segment feedback
    # ------------------------------------------------------------------
    segment_feedback = []
    for seg in seg_stats:
        fb = feedback_for_segment(seg)
        if fb:
            segment_feedback.append(fb)

    # ------------------------------------------------------------------
    # Final output schema
    # ------------------------------------------------------------------
    return {
        "score_0_100": score,
        "label": label,
        "confidence": 0.75,
        "abstained": False,
        "details": {
            "average_wpm": wpm,
            "optimal_range_wpm": [110, 170],
            "segment_stats": seg_stats,
        },
        "feedback": overall_feedback + segment_feedback,
    }
