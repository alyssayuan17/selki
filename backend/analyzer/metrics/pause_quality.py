"""
analyzer/metrics/pause_quality.py

Evaluates pauses using:
- ASR word-based pauses (word_pauses)
- VAD-based silence segments (vad_silence_segments)

Outputs:
- score_0_100
- label ("too_many_pauses" / "too_few_pauses" / "good" / "abstained")
- confidence
- details
- timeline entries for frontend visualization
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple


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
def combine_pauses(
    word_pauses: List[Dict[str, Any]] | None,
    vad_silences: List[Dict[str, Any]] | None,
    duration_sec: float,
    boundary_margin: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Unifies pauses from:
      - Whisper word gaps (word_pauses)
      - VAD silence (vad_silences)

    **Important:** we do NOT treat pure leading/trailing silence as pauses.
    So any VAD silence segment that is:
      - near the very start (start < boundary_margin), or
      - near the very end  (end   > duration_sec - boundary_margin)
    is ignored.
    """
    combined: List[Dict[str, Any]] = []

    # 1) ASR word-based pauses (these are already internal, no need to trim)
    for p in word_pauses or []:
        combined.append({
            "start": float(p["start"]),
            "end": float(p["end"]),
            "duration": float(p["duration"]),
            "source": "asr",
        })

    # 2) VAD-based silences, with boundary trimming
    if vad_silences and duration_sec > 0:
        # if the clip is very short, shrink margin so we don't nuke everything
        margin = min(boundary_margin, duration_sec / 4.0)

        for s in vad_silences:
            start = float(s["start"])
            end = float(s["end"])
            dur = max(0.0, end - start)

            # skip nonsense / zero-length
            if dur <= 0.0:
                continue

            # ignore leading silence near t=0
            if start <= margin:
                continue

            # ignore trailing silence near the end
            if end >= duration_sec - margin:
                continue

            combined.append({
                "start": start,
                "end": end,
                "duration": dur,
                "source": "vad",
            })

    combined.sort(key=lambda x: x["start"])
    return combined


# --------------------------------------------------------
# Main metric function
# --------------------------------------------------------
def compute_pause_quality_metric(
    word_pauses: List[Dict[str, Any]] | None,
    vad_silence_segments: List[Dict[str, Any]] | None,
    duration_sec: float,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Returns:
      (metric_result, timeline_events)
    """

    if duration_sec <= 0:
        return _abstained("invalid_duration")

    combined = combine_pauses(word_pauses, vad_silence_segments, duration_sec)

    if not combined:
        return _abstained("no_pauses_detected")

    durations = [p["duration"] for p in combined]
    avg_pause = sum(durations) / len(durations)

    long_pauses = [d for d in durations if d > 1.0]
    short_pauses = [d for d in durations if d < 0.2]

    # pauses per second
    pause_rate = len(combined) / duration_sec if duration_sec > 0 else 0.0

    # ------------------------------------------
    # Heuristic scoring rules
    # ------------------------------------------
    if pause_rate > 0.30:     # many pauses
        label = "too_many_pauses"
        score = 45
    elif pause_rate < 0.05:   # almost no pauses
        label = "too_few_pauses"
        score = 55
    else:
        label = "good"
        score = 85

    confidence = 0.75

    # ------------------------------------------
    # Construct timeline
    # ------------------------------------------
    timeline: List[Dict[str, Any]] = []
    for p in combined:
        timeline.append({
            "start_sec": p["start"],
            "end_sec": p["end"],
            "type": "pause",
            "quality": classify_pause(p["duration"]),
            "source": p["source"],
        })

    # ------------------------------------------
    # Feedback text
    # ------------------------------------------
    feedback: List[Dict[str, Any]] = []
    if label == "too_many_pauses":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": "You pause very frequently. Try connecting ideas more fluidly.",
            "tip_type": "pause_quality",
        })
    elif label == "too_few_pauses":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": "You rarely pause. Add short pauses to emphasize key transitions.",
            "tip_type": "pause_quality",
        })
    elif label == "good":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": "Your pacing and pauses are balanced and clear.",
            "tip_type": "pause_quality",
        })

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
def _abstained(reason: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    metric = {
        "score_0_100": None,
        "label": "abstained",
        "confidence": 0.0,
        "abstained": True,
        "details": {"reason": reason},
        "feedback": [],
    }
    return metric, []
