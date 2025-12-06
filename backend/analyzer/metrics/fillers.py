"""
analyzer/metrics/fillers.py

Rule-based "fillers" metric:

- Detects common filler tokens from ASR words.
- Computes:
    - total_fillers
    - filler_rate_per_min
    - top_fillers
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
      "details": {...},
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

    return {
        "score_0_100": score,
        "label": label,
        "confidence": confidence,
        "abstained": False,
        "details": {
            "filler_rate_per_min": filler_rate_per_min,
            "total_fillers": total_fillers,
            "top_fillers": top_fillers,
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
