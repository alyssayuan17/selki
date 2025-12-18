"""
analyzer/metrics/fillers.py

Rule-based "fillers" metric:

- Detects common filler tokens from ASR words.
- Computes:
    - total_fillers
    - filler_rate_per_min
    - fillers_per_100_words
    - top_fillers (list of {token, count})
    - filler_spikes (time spans where filler rate exceeds threshold)
- Maps to labels:
    - "low_filler_rate"
    - "moderate_filler_rate"
    - "high_filler_rate"
    - "abstained"
- Produces a metric object:
    {
      "score_0_100": ...,
      "label": "...",
      "confidence": ...,
      "abstained": False,
      "details": {
        "filler_rate_per_min": float,
        "fillers_per_100_words": float,
        "total_fillers": int,
        "top_fillers": [{token: str, count: int}],
        "filler_spikes": [{start_sec: float, end_sec: float, filler_rate: float}]
      },
      "feedback": [...]
    }
"""

from __future__ import annotations
from typing import List, Dict, Any
import string
from collections import Counter


# ---------------------------------------------
# Normalization helpers
# ---------------------------------------------
_PUNCT_TABLE = str.maketrans("", "", string.punctuation)

# Simple single-token filler lexicon.
# (You can expand this anytime.)
FILLER_TOKENS = {
    "um",
    "uh",
    "erm",
    "er",
    "uhm",
    "like",
    "actually",
    "basically",
    "youknow",  # sometimes ASR mashes it
}


def _normalize_token(text: str) -> str:
    """
    Lowercase + strip punctuation + collapse spaces.
    Also handles "you know" -> "youknow" style patterns in a rough way.
    """
    t = text.lower().translate(_PUNCT_TABLE).strip()
    t = " ".join(t.split())
    # crude normalization for "you know"
    if t == "you know":
        t = "youknow"
    return t


def _detect_filler_spikes(
    words: List[Dict[str, Any]],
    window_sec: float = 30.0,
    spike_threshold_per_min: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Detect time spans where filler rate spikes above threshold.

    Uses a sliding window to compute filler rate per minute across the talk.
    Returns time spans where the rate exceeds spike_threshold_per_min.

    Args:
        words: List of word dictionaries with 'text', 'start', 'end' fields
        window_sec: Size of sliding window in seconds (default 30s)
        spike_threshold_per_min: Filler rate threshold to consider a spike (default 10/min)

    Returns:
        List of spike segments: [{"start_sec": ..., "end_sec": ..., "filler_rate": ...}]
    """
    if not words:
        return []

    # Get time bounds
    first_word_start = min(w.get("start", 0) for w in words if "start" in w)
    last_word_end = max(w.get("end", 0) for w in words if "end" in w)
    duration = last_word_end - first_word_start

    if duration <= 0:
        return []

    # Create list of filler word timestamps
    filler_times = []
    for w in words:
        text = w.get("text")
        if not isinstance(text, str):
            continue
        norm = _normalize_token(text)
        if norm in FILLER_TOKENS:
            start_time = w.get("start", 0)
            filler_times.append(start_time)

    if not filler_times:
        return []

    # Slide window across talk, checking filler rate
    spikes = []
    step_sec = window_sec / 4.0  # 25% overlap for smoother detection
    current_start = first_word_start

    while current_start + window_sec <= last_word_end:
        window_end = current_start + window_sec

        # Count fillers in this window
        fillers_in_window = sum(1 for t in filler_times if current_start <= t < window_end)

        # Convert to rate per minute
        window_duration_min = window_sec / 60.0
        filler_rate = fillers_in_window / window_duration_min if window_duration_min > 0 else 0.0

        # Check if this is a spike
        if filler_rate >= spike_threshold_per_min:
            # Check if we can merge with previous spike
            if spikes and abs(spikes[-1]["end_sec"] - current_start) < step_sec:
                # Extend previous spike
                spikes[-1]["end_sec"] = window_end
                spikes[-1]["filler_rate"] = max(spikes[-1]["filler_rate"], filler_rate)
            else:
                # New spike
                spikes.append({
                    "start_sec": current_start,
                    "end_sec": window_end,
                    "filler_rate": filler_rate,
                })

        current_start += step_sec

    return spikes


# ---------------------------------------------
# Main filler metric
# ---------------------------------------------
def compute_fillers_metric(words: List[Dict[str, Any]], duration_sec: float) -> Dict[str, Any]:
    """
    words: list of {"text": ..., "start": ..., "end": ..., "probability": ...}
    duration_sec: total talk duration (seconds)
    """

    if duration_sec <= 0 or not words:
        return _abstained("no_words_or_invalid_duration")

    duration_min = duration_sec / 60.0 if duration_sec > 0 else 1e-6

    # Count filler tokens
    filler_counter: Counter[str] = Counter()
    total_tokens = 0

    for w in words:
        text = w.get("text")
        if not isinstance(text, str):
            continue
        total_tokens += 1
        norm = _normalize_token(text)
        if norm in FILLER_TOKENS:
            filler_counter[norm] += 1

    total_fillers = sum(filler_counter.values())

    # If almost no speech or no words recognized, abstain.
    if total_tokens == 0:
        return _abstained("no_tokens")

    filler_rate_per_min = total_fillers / duration_min if duration_min > 0 else 0.0
    fillers_per_100_words = (total_fillers / total_tokens * 100.0) if total_tokens > 0 else 0.0

    # Detect filler spikes
    filler_spikes = _detect_filler_spikes(words)

    # ---------------------------------------------
    # Map rate → label + score
    # ---------------------------------------------
    # You can tune these thresholds later:
    #   <= 3/min  => low_filler_rate
    #   3–7/min   => moderate_filler_rate
    #   > 7/min   => high_filler_rate
    if total_fillers == 0:
        label = "low_filler_rate"
        score = 95
    elif filler_rate_per_min <= 3:
        label = "low_filler_rate"
        score = 85
    elif filler_rate_per_min <= 7:
        label = "moderate_filler_rate"
        score = 65
    else:
        label = "high_filler_rate"
        score = 45

    # Confidence is just a heuristic for now
    confidence = 0.75

    # Build "top_fillers" list like in your spec
    top_fillers = [
        {"token": tok, "count": count}
        for tok, count in filler_counter.most_common()
    ]

    # ---------------------------------------------
    # Feedback messages
    # ---------------------------------------------
    feedback: List[Dict[str, Any]] = []

    if label == "high_filler_rate":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"High filler rate (~{filler_rate_per_min:.1f}/min). "
                "Try replacing 'um'/'uh' with a silent breath or short pause."
            ),
            "tip_type": "fillers",
        })
    elif label == "moderate_filler_rate":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"Moderate filler rate (~{filler_rate_per_min:.1f}/min). "
                "Being more deliberate before speaking can reduce fillers."
            ),
            "tip_type": "fillers",
        })
    elif label == "low_filler_rate":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"Low filler rate (~{filler_rate_per_min:.1f}/min). "
                "Great job keeping your speech clean and focused."
            ),
            "tip_type": "fillers",
        })

    # Add feedback for specific filler spikes
    for spike in filler_spikes:
        feedback.append({
            "start_sec": spike["start_sec"],
            "end_sec": spike["end_sec"],
            "message": (
                f"High filler rate (~{spike['filler_rate']:.1f}/min) detected in this segment. "
                "Practice pausing silently instead of saying 'um'."
            ),
            "tip_type": "fillers",
        })

    return {
        "score_0_100": score,
        "label": label,
        "confidence": confidence,
        "abstained": False,
        "details": {
            "filler_rate_per_min": filler_rate_per_min,
            "fillers_per_100_words": fillers_per_100_words,
            "total_fillers": total_fillers,
            "top_fillers": top_fillers,
            "filler_spikes": filler_spikes,
        },
        "feedback": feedback,
    }


def _abstained(reason: str) -> Dict[str, Any]:
    return {
        "score_0_100": None,
        "label": "abstained",
        "confidence": 0.0,
        "abstained": True,
        "details": {"reason": reason},
        "feedback": [],
    }
