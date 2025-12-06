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

Algorithm:
- Combines pauses from both ASR and VAD
- When pauses overlap, VAD takes priority (more accurate)
- Boundary silence (start/end) is filtered out
"""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


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
# Helper: check if two pauses overlap
# --------------------------------------------------------
def pauses_overlap(p1: Dict[str, Any], p2: Dict[str, Any], threshold: float = 0.1) -> bool:
    """
    Check if two pause segments overlap significantly.

    Args:
        p1, p2: Pause dictionaries with 'start' and 'end' keys
        threshold: Minimum overlap duration (seconds) to consider as overlapping

    Returns:
        True if pauses overlap by at least threshold seconds
    """
    # Calculate overlap region
    overlap_start = max(p1["start"], p2["start"])
    overlap_end = min(p1["end"], p2["end"])
    overlap_duration = max(0.0, overlap_end - overlap_start)

    return overlap_duration >= threshold


# --------------------------------------------------------
# Helper: merge overlapping pauses, preferring VAD
# --------------------------------------------------------
def merge_overlapping_pauses(pauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge overlapping pauses, giving priority to VAD over ASR.

    Algorithm:
    1. Sort pauses by start time
    2. For each pause, check if it overlaps with previously added pauses
    3. If overlap exists:
       - If one is VAD and one is ASR: keep VAD, discard ASR
       - If both are same type: merge into single pause
    4. If no overlap: add as new pause

    Args:
        pauses: List of pause dicts with 'start', 'end', 'duration', 'source'

    Returns:
        Deduplicated list of pauses with overlaps resolved
    """
    if not pauses:
        return []

    # Sort by start time
    sorted_pauses = sorted(pauses, key=lambda x: x["start"])
    merged: List[Dict[str, Any]] = []

    for current_pause in sorted_pauses:
        if not merged:
            # First pause, just add it
            merged.append(current_pause.copy())
            continue

        # Check if current pause overlaps with any in merged list
        overlapped = False

        for i, existing_pause in enumerate(merged):
            if pauses_overlap(current_pause, existing_pause):
                overlapped = True

                # Determine which to keep based on source priority
                current_source = current_pause["source"]
                existing_source = existing_pause["source"]

                if current_source == "vad" and existing_source == "asr":
                    # Replace ASR with VAD (VAD is more accurate)
                    merged[i] = current_pause.copy()
                    logger.debug(f"Replaced ASR pause [{existing_pause['start']:.2f}-{existing_pause['end']:.2f}] "
                               f"with overlapping VAD pause [{current_pause['start']:.2f}-{current_pause['end']:.2f}]")

                elif current_source == "asr" and existing_source == "vad":
                    # Keep VAD, ignore ASR
                    logger.debug(f"Skipped ASR pause [{current_pause['start']:.2f}-{current_pause['end']:.2f}] "
                               f"- overlaps with VAD pause [{existing_pause['start']:.2f}-{existing_pause['end']:.2f}]")
                    pass  # Don't add current pause

                else:
                    # Both same type - merge into longer/combined interval
                    merged_start = min(existing_pause["start"], current_pause["start"])
                    merged_end = max(existing_pause["end"], current_pause["end"])
                    merged_duration = merged_end - merged_start

                    merged[i] = {
                        "start": merged_start,
                        "end": merged_end,
                        "duration": merged_duration,
                        "source": existing_source,  # Keep original source
                    }
                    logger.debug(f"Merged two {existing_source} pauses: "
                               f"[{existing_pause['start']:.2f}-{existing_pause['end']:.2f}] + "
                               f"[{current_pause['start']:.2f}-{current_pause['end']:.2f}] -> "
                               f"[{merged_start:.2f}-{merged_end:.2f}]")

                break  # Only merge with first overlap found

        if not overlapped:
            # No overlap, add as new pause
            merged.append(current_pause.copy())

    # Sort final result by start time
    merged.sort(key=lambda x: x["start"])

    logger.debug(f"Pause deduplication: {len(pauses)} input pauses -> {len(merged)} merged pauses")
    return merged


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

    **Important:**
    1. We do NOT treat pure leading/trailing silence as pauses.
       - Any VAD silence near the very start (start < boundary_margin)
       - Any VAD silence near the very end (end > duration_sec - boundary_margin)
       is ignored.

    2. Overlapping pauses are merged, with VAD taking priority over ASR.
       - If VAD and ASR overlap: VAD wins (more accurate)
       - If two of same type overlap: they are merged

    Returns:
        Deduplicated list of pauses sorted by start time
    """
    all_pauses: List[Dict[str, Any]] = []

    # 1) ASR word-based pauses (these are already internal, no need to trim)
    for p in word_pauses or []:
        all_pauses.append({
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

            all_pauses.append({
                "start": start,
                "end": end,
                "duration": dur,
                "source": "vad",
            })

    # 3) Merge overlapping pauses, giving priority to VAD
    logger.debug(f"Before merging: {len(all_pauses)} pauses "
                f"({len([p for p in all_pauses if p['source'] == 'asr'])} ASR, "
                f"{len([p for p in all_pauses if p['source'] == 'vad'])} VAD)")

    merged_pauses = merge_overlapping_pauses(all_pauses)

    logger.debug(f"After merging: {len(merged_pauses)} pauses "
                f"({len([p for p in merged_pauses if p['source'] == 'asr'])} ASR, "
                f"{len([p for p in merged_pauses if p['source'] == 'vad'])} VAD)")

    return merged_pauses


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
