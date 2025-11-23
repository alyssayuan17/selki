"""
analyzer/metrics/pause_quality.py

Evaluates pauses using:
- ASR word-based pauses (word_pauses)
- VAD-based silence segments (vad_silence_segments)

Outputs:
- score_0_100
- label ("too_many_pauses" / "too_few_pauses" / "good")
- confidence
- details
- timeline entries for frontend visualization
"""

from __future__ import annotations
from typing import List, Dict, Any


# --------------------------------------------------------
# Helper: classify pause duration
# --------------------------------------------------------
def classify_pause(duration: float) -> str:
    if duration < 0.2:
        return "very_short"
    if duration < 0.5:
        return "short"
    if duration < 1.0:
        return "medium"
    return "long"


# --------------------------------------------------------
# Build combined pause list
# --------------------------------------------------------
def combine_pauses(word_pauses, vad_silences):
    """Unifies pauses from Whisper word gaps & VAD silence."""
    combined = []

    for p in word_pauses or []:
        combined.append({
            "start": p["start"],
            "end": p["end"],
            "duration": p["duration"],
            "source": "asr"
        })

    for s in vad_silences or []:
        combined.append({
            "start": s["start"],
            "end": s["end"],
            "duration": s["end"] - s["start"],
            "source": "vad"
        })

    combined.sort(key=lambda x: x["start"])
    return combined


# --------------------------------------------------------
# Main metric function
# --------------------------------------------------------
def compute_pause_quality_metric(
    word_pauses: List[Dict[str, Any]],
    vad_silence_segments: List[Dict[str, Any]],
    duration_sec: float
) -> (Dict[str, Any]):
    """
    Returns:
      metric_result, timeline_events
    """

    combined = combine_pauses(word_pauses, vad_silence_segments)

    if duration_sec <= 0:
        return _abstained("invalid_duration")

    if not combined:
        return _abstained("no_pauses_detected")

    durations = [p["duration"] for p in combined]
    avg_pause = sum(durations) / len(durations)

    long_pauses = [d for d in durations if d > 1.0]
    short_pauses = [d for d in durations if d < 0.2]

    pause_rate = len(combined) / duration_sec  # pauses per second

    # ------------------------------------------
    # Heuristic scoring rules
    # ------------------------------------------

    if pause_rate > 0.30:     # too many pauses
        label = "too_many_pauses"
        score = 45
    elif pause_rate < 0.05:   # speaking without pauses
        label = "too_few_pauses"
        score = 55
    else:
        label = "good"
        score = 85

    confidence = 0.75

    # ------------------------------------------
    # Construct timeline
    # ------------------------------------------
    timeline = []
    for p in combined:
        timeline.append({
            "start_sec": p["start"],
            "end_sec": p["end"],
            "type": "pause",
            "quality": classify_pause(p["duration"]),
            "source": p["source"]
        })

    # ------------------------------------------
    # Feedback text
    # ------------------------------------------

    feedback = []
    if label == "too_many_pauses":
        feedback.append({
            "start_sec": 0,
            "end_sec": duration_sec,
            "message": "You pause very frequently. Try connecting ideas more fluidly.",
            "tip_type": "pause_quality",
        })

    elif label == "too_few_pauses":
        feedback.append({
            "start_sec": 0,
            "end_sec": duration_sec,
            "message": "You rarely pause. Add short pauses to emphasize key transitions.",
            "tip_type": "pause_quality",
        })

    elif label == "good":
        feedback.append({
            "start_sec": 0,
            "end_sec": duration_sec,
            "message": "Your pacing and pauses are balanced and clear.",
            "tip_type": "pause_quality",
        })

    # ------------------------------------------
    # Final metric object
    # ------------------------------------------
    metric = {
        "score_0_100": score,
        "label": label,
        "confidence": confidence,
        "abstained": False,
        "details": {
            "total_pauses": len(combined),
            "average_pause_duration": avg_pause,
            "long_pauses": len(long_pauses),
            "short_pauses": len(short_pauses),
            "pause_rate": pause_rate,
        },
        "feedback": feedback,
    }

    return metric, timeline


# --------------------------------------------------------
# Helper: abstainment
# --------------------------------------------------------
def _abstained(reason: str):
    metric = {
        "score_0_100": None,
        "label": "abstained",
        "confidence": 0.0,
        "abstained": True,
        "details": {"reason": reason},
        "feedback": [],
    }
    return metric, []
