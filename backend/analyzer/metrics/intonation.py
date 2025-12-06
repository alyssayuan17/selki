"""
analyzer/metrics/intonation.py

Rule-based "intonation" metric.

Uses summary prosody features from audio_to_json:
- pitch_std_hz (variation in pitch)
- mean_pitch_hz (for context)
- energy_std (variation in loudness)
- mean_energy (average loudness)

Enhanced with:
- pitch_range_hz (estimated from std)
- pitch_cov (coefficient of variation = std / mean)
- multi-factor classification combining pitch_std, pitch_range, energy

Outputs one of:
    "monotone", "somewhat_monotone", "dynamic", or "abstained"

Schema:
{
  "score_0_100": ...,
  "label": "...",
  "confidence": ...,
  "abstained": bool,
  "details": {
      "mean_pitch_hz": ...,
      "pitch_std_hz": ...,
      "pitch_range_hz": ...,        # NEW: estimated pitch range
      "pitch_cov": ...,              # NEW: coefficient of variation
      "energy_mean": ...,
      "energy_std": ...,
      "prosody_variance_score": ...
  },
  "feedback": [...]
}
"""

from __future__ import annotations
from typing import Dict, Any, Optional


# ----------------------------------------------------
# Helper: Compute exact pitch range from raw data
# ----------------------------------------------------
def compute_exact_pitch_range(raw_pitch_hz: Optional[list]) -> Optional[float]:
    """
    Compute exact pitch range from raw pitch timeseries.

    Args:
        raw_pitch_hz: List of F0 values per frame (NaN for unvoiced frames)

    Returns:
        Exact pitch range (max - min) in Hz, or None if no valid data

    Note:
        Uses 5th-95th percentile to exclude outliers from pitch tracking errors.
        Raw F0 from librosa.yin can have spurious octave jumps or noise-induced
        false detections that should be filtered out.
    """
    if raw_pitch_hz is None or len(raw_pitch_hz) == 0:
        return None

    # Filter out unvoiced frames (NaN or zero values)
    import numpy as np
    pitch_array = np.array(raw_pitch_hz)
    voiced = pitch_array[~np.isnan(pitch_array) & (pitch_array > 0)]

    if len(voiced) < 10:  # Need at least 10 voiced frames
        return None

    # Use percentiles to exclude outliers (5th-95th percentile)
    # This removes pitch tracking errors (octave jumps, spurious detections)
    p5 = np.percentile(voiced, 5)
    p95 = np.percentile(voiced, 95)
    pitch_range = float(p95 - p5)
    return pitch_range


# ----------------------------------------------------
# Helper: Estimate pitch range from std (fallback)
# ----------------------------------------------------
def estimate_pitch_range(
    mean_pitch_hz: Optional[float],
    pitch_std_hz: Optional[float],
) -> Optional[float]:
    """
    Estimate pitch range using statistical heuristic (fallback when raw data unavailable).

    Assuming pitch follows roughly normal distribution,
    range ≈ 2 * std * k, where k is coverage factor.
    For ~95% coverage, k ≈ 2, so range ≈ 4 * std.

    This is a rough estimate - actual range from raw data is better.
    """
    if mean_pitch_hz is None or pitch_std_hz is None:
        return None

    # Heuristic: range ≈ 4 * std (covers ~95% of values)
    estimated_range = 4.0 * pitch_std_hz
    return float(estimated_range)


# ----------------------------------------------------
# Helper: Compute coefficient of variation
# ----------------------------------------------------
def compute_pitch_cov(
    mean_pitch_hz: Optional[float],
    pitch_std_hz: Optional[float],
) -> Optional[float]:
    """
    Coefficient of variation (CoV) = std / mean

    Normalizes pitch variance by speaker's mean pitch,
    making it speaker-independent.

    Typical values:
    - CoV < 0.10 → monotone
    - CoV 0.10-0.20 → moderate variation
    - CoV > 0.20 → dynamic
    """
    if mean_pitch_hz is None or pitch_std_hz is None:
        return None
    if mean_pitch_hz <= 0:
        return None

    return float(pitch_std_hz / mean_pitch_hz)


# ----------------------------------------------------
# Helper: Multi-factor labeling (ENHANCED)
# ----------------------------------------------------
def label_from_prosody_factors(
    pitch_std_hz: Optional[float],
    pitch_range_hz: Optional[float],
    pitch_cov: Optional[float],
    energy_std: Optional[float],
) -> str:
    """
    Multi-factor classification using:
    - pitch_std_hz: Standard deviation of pitch
    - pitch_range_hz: Estimated pitch range
    - pitch_cov: Coefficient of variation (std/mean)
    - energy_std: Standard deviation of energy

    This is more robust than using pitch_std alone.

    Thresholds (tunable):
    - pitch_std: < 12 Hz (monotone), 12-25 Hz (moderate), > 25 Hz (dynamic)
    - pitch_range: < 50 Hz (monotone), 50-100 Hz (moderate), > 100 Hz (dynamic)
    - pitch_cov: < 0.10 (monotone), 0.10-0.20 (moderate), > 0.20 (dynamic)
    - energy_std: < 0.005 (monotone), 0.005-0.02 (moderate), > 0.02 (dynamic)
    """
    if pitch_std_hz is None:
        return "monotone"

    # Calculate component scores (0 = monotone, 1 = moderate, 2 = dynamic)
    pitch_std_score = 0
    if pitch_std_hz < 12:
        pitch_std_score = 0
    elif pitch_std_hz < 25:
        pitch_std_score = 1
    else:
        pitch_std_score = 2

    pitch_range_score = 0
    if pitch_range_hz is not None:
        if pitch_range_hz < 50:      # Less than half octave
            pitch_range_score = 0
        elif pitch_range_hz < 100:   # Less than 1 octave
            pitch_range_score = 1
        else:                         # More than 1 octave
            pitch_range_score = 2

    cov_score = 0
    if pitch_cov is not None:
        if pitch_cov < 0.10:
            cov_score = 0
        elif pitch_cov < 0.20:
            cov_score = 1
        else:
            cov_score = 2

    energy_score = 0
    if energy_std is not None:
        if energy_std < 0.005:
            energy_score = 0
        elif energy_std < 0.02:
            energy_score = 1
        else:
            energy_score = 2

    # Weighted average (prioritize pitch metrics)
    total_score = (
        0.35 * pitch_std_score +    # Variance is important
        0.25 * pitch_range_score +  # Range is important
        0.25 * cov_score +           # CoV is speaker-independent
        0.15 * energy_score          # Energy is supplementary
    )

    # Map aggregate score to label
    if total_score < 0.7:
        return "monotone"
    elif total_score < 1.4:
        return "somewhat_monotone"
    else:
        return "dynamic"


# ----------------------------------------------------
# Helper: label → score
# ----------------------------------------------------
def score_from_label(label: str) -> int:
    mapping = {
        "monotone": 45,
        "somewhat_monotone": 65,
        "dynamic": 85,
    }
    return mapping.get(label, 0)


# ----------------------------------------------------
# Helper: combine pitch/energy into [0, 1] score
# ----------------------------------------------------
def prosody_variance_score(
    pitch_std_hz: Optional[float],
    energy_std: Optional[float],
) -> float:
    """
    Crude normalization of pitch_std_hz and energy_std into [0, 1].

    Idea:
      - Assume "interesting" speakers typically have pitch_std in ~[10, 50] Hz
      - Clip into that range and rescale
      - Do similar for energy_std and average

    This is just a placeholder; replace later with a learned calibration.
    """
    def norm(x: Optional[float], lo: float, hi: float) -> float:
        if x is None:
            return 0.0
        x_clipped = max(lo, min(hi, x))
        return (x_clipped - lo) / (hi - lo)  # 0..1

    pitch_score = norm(pitch_std_hz, lo=5.0, hi=50.0)
    energy_score = norm(energy_std, lo=0.001, hi=0.05)

    return float(0.5 * (pitch_score + energy_score))


# ----------------------------------------------------
# Main entrypoint
# ----------------------------------------------------
def compute_intonation_metric(
    audio_features: Dict[str, Any],
    duration_sec: float,
    raw_pitch_hz: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Compute intonation metric from audio features.

    Args:
        audio_features: Dict from audio_json["audio_features"]:
            {
                "mean_pitch_hz": ...,
                "pitch_std_hz": ...,
                "mean_energy": ...,
                "energy_std": ...
            }
        duration_sec: Audio duration in seconds
        raw_pitch_hz: Optional raw F0 timeseries for exact pitch range calculation
                     (list of float values, NaN for unvoiced frames)

    Returns:
        Metric dict with score, label, confidence, details, feedback
    """

    # If talk is extremely short, abstain (not enough context)
    if duration_sec <= 3.0:
        return {
            "score_0_100": None,
            "label": "abstained",
            "confidence": 0.0,
            "abstained": True,
            "details": {"reason": "talk_too_short_for_intonation"},
            "feedback": [],
        }

    mean_pitch_hz = audio_features.get("mean_pitch_hz")
    pitch_std_hz = audio_features.get("pitch_std_hz")
    energy_mean = audio_features.get("mean_energy")
    energy_std = audio_features.get("energy_std")

    # If we have no pitch info at all, abstain
    if pitch_std_hz is None:
        return {
            "score_0_100": None,
            "label": "abstained",
            "confidence": 0.0,
            "abstained": True,
            "details": {"reason": "no_pitch_data"},
            "feedback": [],
        }

    # -------------------------
    # NEW: Compute additional factors
    # -------------------------
    # Try to compute exact pitch range from raw data first, fall back to estimate
    pitch_range_hz = compute_exact_pitch_range(raw_pitch_hz)
    if pitch_range_hz is None:
        # Fallback to statistical estimate
        pitch_range_hz = estimate_pitch_range(mean_pitch_hz, pitch_std_hz)

    pitch_cov = compute_pitch_cov(mean_pitch_hz, pitch_std_hz)

    # Use enhanced multi-factor labeling
    label = label_from_prosody_factors(
        pitch_std_hz=pitch_std_hz,
        pitch_range_hz=pitch_range_hz,
        pitch_cov=pitch_cov,
        energy_std=energy_std,
    )

    score = score_from_label(label)
    prosody_score = prosody_variance_score(pitch_std_hz, energy_std)

    # Very rough confidence heuristic: higher variance → higher confidence
    # Also factor in whether we have all metrics
    confidence = 0.6 + 0.3 * prosody_score  # in [0.6, 0.9] roughly
    if pitch_range_hz is not None and pitch_cov is not None:
        confidence = min(0.95, confidence + 0.05)  # Boost if we have all factors

    # -------------------------
    # Enhanced Feedback with specific values
    # -------------------------
    feedback = []

    # Determine if range is exact or estimated
    has_exact_range = compute_exact_pitch_range(raw_pitch_hz) is not None
    range_qualifier = "" if has_exact_range else "~"  # ~ indicates estimate

    if label == "monotone":
        # Show actual values to make feedback actionable
        pitch_range_str = f"{range_qualifier}{pitch_range_hz:.0f} Hz" if pitch_range_hz else "unknown"
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"Your pitch stays relatively flat (variation: {pitch_std_hz:.1f} Hz, "
                f"range: {pitch_range_str}). "
                f"Try varying your pitch by at least 100-150 Hz (about 1 octave) "
                f"to sound more engaging. Emphasize key words with pitch rises."
            ),
            "tip_type": "intonation",
        })
    elif label == "somewhat_monotone":
        pitch_range_str = f"{range_qualifier}{pitch_range_hz:.0f} Hz" if pitch_range_hz else "unknown"
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"You have some pitch variation (std: {pitch_std_hz:.1f} Hz, range: {pitch_range_str}), "
                f"but could be more dynamic. "
                f"Try increasing your pitch range to >100 Hz by using pitch rises "
                f"for questions and pitch falls for emphasis."
            ),
            "tip_type": "intonation",
        })
    elif label == "dynamic":
        pitch_range_str = f"{range_qualifier}{pitch_range_hz:.0f} Hz" if pitch_range_hz else "unknown"
        feedback.append({
            "start_sec": 0.0,
            "end_sec": duration_sec,
            "message": (
                f"Excellent! Your pitch varies dynamically (std: {pitch_std_hz:.1f} Hz, range: {pitch_range_str}), "
                f"which helps maintain listener attention. "
                f"Keep using vocal variety to emphasize structure and key points."
            ),
            "tip_type": "intonation",
        })

    return {
        "score_0_100": score,
        "label": label,
        "confidence": float(confidence),
        "abstained": False,
        "details": {
            "mean_pitch_hz": mean_pitch_hz,
            "pitch_std_hz": pitch_std_hz,
            "pitch_range_hz": pitch_range_hz,      # NEW
            "pitch_cov": pitch_cov,                 # NEW
            "energy_mean": energy_mean,             # NEW
            "energy_std": energy_std,
            "prosody_variance_score": prosody_score,
        },
        "feedback": feedback,
    }
