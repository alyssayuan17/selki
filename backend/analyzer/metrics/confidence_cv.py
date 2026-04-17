"""
analyzer/metrics/confidence_cv.py

Rule-based "confidence" metric derived from:
- Filler rate (fewer fillers → more confident)
- Pace consistency (lower segment WPM variance → steadier delivery)
- Intonation variation (some pitch variation is good; monotone = low confidence)
- Pause quality ratio (more good pauses than bad = confident structure)
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional


# ── Helpers ────────────────────────────────────────────────────────────────

FILLER_WORDS = {
    "uh", "um", "uh-huh", "hmm", "er", "ah",
    "like", "you know", "sort of", "kind of", "basically",
}


def _filler_rate(words: List[Dict[str, Any]], duration_sec: float) -> float:
    """Fillers per minute."""
    if duration_sec <= 0:
        return 0.0
    count = sum(1 for w in words if w.get("text", "").strip().lower() in FILLER_WORDS)
    return (count / duration_sec) * 60.0


def _pace_consistency(words: List[Dict[str, Any]], duration_sec: float) -> float:
    """
    Coefficient of variation of per-30s segment WPM.
    Lower = more consistent = more confident.
    Returns CoV in [0, ∞); capped at 1.0 for scoring.
    """
    if not words or duration_sec <= 0:
        return 1.0

    segment_length = 30.0
    wpms: List[float] = []
    t = 0.0
    while t < duration_sec:
        seg_end = min(t + segment_length, duration_sec)
        seg_words = [w for w in words if t <= w.get("start", 0.0) < seg_end]
        seg_dur = seg_end - t
        if seg_dur > 0:
            wpms.append(len(seg_words) / (seg_dur / 60.0))
        t += segment_length

    if len(wpms) < 2:
        return 0.0  # only one segment — can't measure variance

    mean = statistics.mean(wpms)
    if mean == 0:
        return 1.0
    return statistics.stdev(wpms) / mean


def _pitch_variation_score(audio_features: Dict[str, Any]) -> float:
    """
    Map pitch CoV to a 0-1 confidence contribution.
    Too low = monotone (low confidence), optimal band = 0.05-0.25, too high = erratic.
    """
    cov = audio_features.get("pitch_cov") or audio_features.get("pitch_coefficient_of_variation")
    if cov is None:
        return 0.5  # neutral if no data

    cov = float(cov)
    if cov < 0.05:
        # Monotone
        return 0.3
    if cov <= 0.25:
        # Natural variation — good
        return 1.0 - abs(cov - 0.15) / 0.15 * 0.3  # peak at ~0.15
    # Too erratic
    return max(0.2, 1.0 - (cov - 0.25) * 2.0)


def _pause_quality_score(pause_details: Optional[Dict[str, Any]]) -> float:
    """Use the pause_quality metric's good/bad ratio if available."""
    if not pause_details:
        return 0.5

    good = pause_details.get("good_pauses", 0) or 0
    bad = pause_details.get("bad_pauses", 0) or 0
    total = good + bad
    if total == 0:
        return 0.5
    return good / total


# ── Main entrypoint ────────────────────────────────────────────────────────

def compute_confidence_cv_metric(
    words: List[Dict[str, Any]],
    duration_sec: float,
    audio_features: Optional[Dict[str, Any]] = None,
    pause_metric: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Aggregate confidence score from four sub-signals.

    Args:
        words:          list of word-timing dicts (start, end, text)
        duration_sec:   total audio duration
        audio_features: dict from audio_to_json (pitch_cov, mean_pitch, etc.)
        pause_metric:   output of compute_pause_quality_metric (for good/bad pause counts)
    """
    if not words or duration_sec <= 0:
        return {
            "score_0_100": None,
            "label": "abstained",
            "confidence": 0.0,
            "abstained": True,
            "details": {"reason": "no_words"},
            "feedback": [],
        }

    af = audio_features or {}

    # ── Sub-scores (all 0-1) ────────────────────────────────────────────────

    # 1. Filler penalty: 0 fpm → 1.0; ≥10 fpm → 0.0
    fpm = _filler_rate(words, duration_sec)
    filler_score = max(0.0, 1.0 - fpm / 10.0)

    # 2. Pace consistency: CoV 0 → 1.0; CoV ≥0.5 → 0.0
    cov = _pace_consistency(words, duration_sec)
    pace_score = max(0.0, 1.0 - cov / 0.5)

    # 3. Pitch variation (natural expressiveness)
    pitch_score = _pitch_variation_score(af)

    # 4. Pause quality
    pause_details = pause_metric.get("details") if pause_metric else None
    pq_score = _pause_quality_score(pause_details)

    # ── Weighted aggregate ──────────────────────────────────────────────────
    weights = {"filler": 0.35, "pace": 0.25, "pitch": 0.20, "pause": 0.20}
    composite = (
        weights["filler"] * filler_score
        + weights["pace"] * pace_score
        + weights["pitch"] * pitch_score
        + weights["pause"] * pq_score
    )

    score = round(composite * 100)

    # ── Label ───────────────────────────────────────────────────────────────
    if score >= 75:
        label = "confident"
    elif score >= 50:
        label = "moderately_confident"
    elif score >= 30:
        label = "uncertain"
    else:
        label = "low_confidence"

    # ── Feedback ─────────────────────────────────────────────────────────────
    feedback = []

    if label == "confident":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": "Your delivery sounds confident — good pace consistency, minimal fillers, and natural intonation.",
            "tip_type": "confidence",
        })
    elif label == "moderately_confident":
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": "Your delivery is generally confident with some areas to improve.",
            "tip_type": "confidence",
        })
    else:
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": "Your delivery may come across as hesitant. Focus on reducing fillers and steadying your pace.",
            "tip_type": "confidence",
        })

    if fpm >= 5:
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": f"High filler rate ({fpm:.1f} per minute) reduces perceived confidence. Practice pausing instead of filling.",
            "tip_type": "confidence",
        })

    if cov > 0.3:
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": "Your speaking pace varies a lot between segments. A steadier pace helps listeners follow you.",
            "tip_type": "confidence",
        })

    return {
        "score_0_100": score,
        "label": label,
        "confidence": 0.65,
        "abstained": False,
        "details": {
            "filler_rate_per_min": round(fpm, 2),
            "pace_cov": round(cov, 3),
            "filler_score": round(filler_score, 3),
            "pace_consistency_score": round(pace_score, 3),
            "pitch_variation_score": round(pitch_score, 3),
            "pause_quality_score": round(pq_score, 3),
        },
        "feedback": feedback,
    }
