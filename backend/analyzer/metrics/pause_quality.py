"""
analyzer/metrics/pause_quality.py

Evaluates pauses using:
- ASR word-based pauses (word_pauses)
- VAD-based silence segments (vad_silence_segments)
- Word context for helpful/awkward classification

Outputs:
- score_0_100
- label ("too_many_pauses" / "too_few_pauses" / "good" / "abstained")
- confidence
- details:
    - total_pauses, average_pause_duration
    - long_pauses, short_pauses, pause_rate
    - helpful_ratio, awkward_ratio (NEW)
    - helpful_count, awkward_count (NEW)
- timeline entries with context classification (NEW: "helpful" or "awkward")
- feedback with context-aware suggestions

Algorithm:
- Combines pauses from both ASR and VAD
- When pauses overlap, VAD takes priority (more accurate)
- Boundary silence (start/end) is filtered out
- Classifies pauses as helpful (after sentences, signposts) or awkward (mid-phrase, too short/long)
"""

from __future__ import annotations
import logging
from typing import List, Dict, Any, Tuple
import re

logger = logging.getLogger(__name__)

# Signpost phrases that indicate good pause points
SIGNPOST_PATTERNS = [
    r'\b(first|second|third|next|then|finally|lastly)\b',
    r'\b(however|therefore|thus|consequently|moreover|furthermore)\b',
    r'\b(in summary|in conclusion|to conclude|to summarize)\b',
    r'\b(for example|for instance|such as)\b',
    r'\b(on the other hand|in contrast|alternatively)\b',
]

# Compile patterns for efficiency
SIGNPOST_REGEX = [re.compile(p, re.IGNORECASE) for p in SIGNPOST_PATTERNS]


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
# Helper: classify pause as helpful or awkward
# --------------------------------------------------------
def _classify_pause_context(
    pause: Dict[str, Any],
    words: List[Dict[str, Any]]
) -> str:
    """
    Classify a pause as 'helpful' or 'awkward' based on linguistic context.

    Helpful pauses:
    - After sentence-ending punctuation (. ! ?)
    - Before/after signpost phrases (first, however, in conclusion, etc.)
    - Between distinct clauses (after commas in long sentences)
    - Medium duration (0.3-1.5s) that allows processing time

    Awkward pauses:
    - Mid-word or very short word gaps (< 0.2s)
    - Very long pauses (> 2.0s) without clear reason
    - In the middle of common phrases

    Args:
        pause: Pause dict with 'start', 'end', 'duration'
        words: List of word dicts with 'text', 'start', 'end'

    Returns:
        'helpful' or 'awkward'
    """
    pause_start = pause["start"]
    pause_duration = pause["duration"]

    # Very short pauses are generally awkward (likely artifacts)
    if pause_duration < 0.2:
        return "awkward"

    # Very long pauses (> 2.5s) are usually awkward unless at a major boundary
    if pause_duration > 2.5:
        # Could be helpful if after a sentence or before a signpost
        # but default to awkward for very long pauses
        pass  # Will check context below

    # Find words immediately before and after the pause
    word_before = None
    word_after = None

    for w in words:
        w_end = w.get("end", 0)
        w_start = w.get("start", 0)

        # Word that ends just before pause
        if w_end <= pause_start and (word_before is None or w_end > word_before.get("end", 0)):
            word_before = w

        # Word that starts just after pause
        if w_start >= pause["end"] and (word_after is None or w_start < word_after.get("start", float('inf'))):
            word_after = w

    # Build context string for pattern matching
    context_before = word_before.get("text", "") if word_before else ""
    context_after = word_after.get("text", "") if word_after else ""

    # Check if pause follows sentence-ending punctuation
    if context_before and any(context_before.strip().endswith(p) for p in ['.', '!', '?']):
        return "helpful"

    # Check if pause is near a signpost phrase
    context_text = f"{context_before} {context_after}".lower()
    for pattern in SIGNPOST_REGEX:
        if pattern.search(context_text):
            return "helpful"

    # Check if pause follows a comma (clause boundary)
    if context_before and context_before.strip().endswith(','):
        # Helpful if medium duration (0.3-1.2s)
        if 0.3 <= pause_duration <= 1.2:
            return "helpful"

    # Medium-length pauses (0.4-1.5s) are generally helpful for processing
    if 0.4 <= pause_duration <= 1.5:
        return "helpful"

    # Very long pauses without clear reason are awkward
    if pause_duration > 2.0:
        return "awkward"

    # Short pauses (0.2-0.4s) without clear context are slightly awkward
    if pause_duration < 0.4:
        return "awkward"

    # Default: neutral pauses are considered helpful
    return "helpful"


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
    words: List[Dict[str, Any]] | None = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Returns:
      (metric_result, timeline_events)

    Args:
        word_pauses: List of pause dicts from ASR word gaps
        vad_silence_segments: List of silence segments from VAD
        duration_sec: Total duration of the audio
        words: List of word dicts with 'text', 'start', 'end' (optional, for context analysis)
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

    # Classify pauses as helpful or awkward if we have word context
    helpful_count = 0
    awkward_count = 0
    pause_classifications = []

    if words:
        for p in combined:
            context_class = _classify_pause_context(p, words)
            pause_classifications.append(context_class)
            if context_class == "helpful":
                helpful_count += 1
            else:
                awkward_count += 1
    else:
        # Fallback: simple duration-based classification
        for p in combined:
            # Medium pauses (0.3-1.5s) are helpful, others are awkward
            if 0.3 <= p["duration"] <= 1.5:
                pause_classifications.append("helpful")
                helpful_count += 1
            else:
                pause_classifications.append("awkward")
                awkward_count += 1

    # Compute ratios
    total_pauses = len(combined)
    helpful_ratio = helpful_count / total_pauses if total_pauses > 0 else 0.0
    awkward_ratio = awkward_count / total_pauses if total_pauses > 0 else 0.0

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
    for i, p in enumerate(combined):
        timeline_entry = {
            "start_sec": p["start"],
            "end_sec": p["end"],
            "type": "pause",
            "quality": classify_pause(p["duration"]),
            "source": p["source"],
        }
        # Add helpful/awkward classification
        if i < len(pause_classifications):
            timeline_entry["context"] = pause_classifications[i]
        timeline.append(timeline_entry)

    # ------------------------------------------
    # Feedback text
    # ------------------------------------------
    feedback: List[Dict[str, Any]] = []

    # Overall pause rate feedback
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

    # Feedback about helpful vs awkward pauses
    if awkward_ratio > 0.5:
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"{awkward_ratio*100:.0f}% of your pauses are awkwardly placed. "
                "Try pausing after complete thoughts or signpost phrases."
            ),
            "tip_type": "pause_quality",
        })
    elif helpful_ratio > 0.7:
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"{helpful_ratio*100:.0f}% of your pauses are well-placed, "
                "helping listeners process your ideas."
            ),
            "tip_type": "pause_quality",
        })

    # Specific feedback for awkward pauses
    if words:
        for i, p in enumerate(combined):
            if i < len(pause_classifications) and pause_classifications[i] == "awkward":
                # Only report very awkward ones (very short or very long)
                if p["duration"] < 0.2 or p["duration"] > 2.5:
                    feedback.append({
                        "start_sec": p["start"],
                        "end_sec": p["end"],
                        "message": (
                            f"Awkward {p['duration']:.1f}s pause. "
                            f"{'This pause is too short.' if p['duration'] < 0.2 else 'This pause is too long - try to keep pauses under 2 seconds.'}"
                        ),
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
            "helpful_ratio": helpful_ratio,
            "awkward_ratio": awkward_ratio,
            "helpful_count": helpful_count,
            "awkward_count": awkward_count,
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
