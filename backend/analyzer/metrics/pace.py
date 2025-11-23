"""
Hybrid pace metric:
- rule-based → fallback + interpretable features
- regressor → fine-grained prediction

Final pace_score = 0.5*rule_score_norm + 0.5*regressor_score
"""

from __future__ import annotations
from typing import List, Dict, Any
import numpy as np
from pathlib import Path

from analyzer.models.pace_regressor import PaceRegressor, PaceRegressorConfig
from analyzer.metrics.pace_rules import compute_wpm, compute_segment_wpm, label_from_wpm, score_from_label


# --------------------------------------------
# Hybrid pace computation
# --------------------------------------------
def compute_pace_metric(words: List[Dict[str, Any]], duration_sec: float,
                        noise_summary: Dict[str, Any]) -> Dict[str, Any]:

    if not words or duration_sec <= 0:
        return {
            "score_0_100": None,
            "label": "abstained",
            "confidence": 0.0,
            "abstained": True,
            "details": {"reason": "no_words"},
            "feedback": [],
        }

    # ---------------------------
    # RULE-BASED features
    # ---------------------------
    wpm = compute_wpm(words, duration_sec)
    rule_label = label_from_wpm(wpm)
    rule_score = score_from_label(rule_label)  # 40/90/50
    rule_score_norm = rule_score / 100.0       # normalize → [0,1]

    # pause stats (derived from words)
    timestamps = [w["start"] for w in words] + [words[-1]["end"]]
    pauses = np.diff(timestamps)
    mean_pause = float(np.mean(pauses)) if len(pauses) > 0 else 0.0
    pause_ratio = float(sum(p > 0.4 for p in pauses)) / max(len(pauses), 1)

    speech_ratio = noise_summary.get("speech_ratio", 0.0)

    # ---------------------------
    # REGRESSOR features
    # ---------------------------
    features = {
        "overall_wpm": wpm,
        "mean_pause": mean_pause,
        "pause_ratio": pause_ratio,
        "speech_ratio": speech_ratio,
    }

    # Load or initialize regressor
    config = PaceRegressorConfig()
    model_path = Path("backend/analyzer/models/pace_regressor.json") # need to fix??? to be "relative to this file"

    if model_path.exists():
        model = PaceRegressor.load(model_path, config)
    else:
        # cold-start: random model (not ideal)
        model = PaceRegressor(config)

    regressor_score = model.predict(features)  # ∈ [0,1]

    # ---------------------------
    # HYBRID SCORE
    # ---------------------------
    final_score_norm = 0.5 * rule_score_norm + 0.5 * regressor_score
    final_score = int(final_score_norm * 100)

    # ---------------------------
    # Determine final label
    # ---------------------------
    if final_score_norm < 0.33:
        label = "too_slow"
    elif final_score_norm < 0.66:
        label = "optimal"
    else:
        label = "too_fast"

    # ---------------------------
    # Feedback
    # ---------------------------
    feedback = []
    if label == "too_fast":
        feedback.append({
            "message": "Your speaking pace is fast. Add strategic pauses.",
            "tip_type": "pace",
            "start_sec": 0.0,
            "end_sec": min(duration_sec, 30.0),
        })
    elif label == "too_slow":
        feedback.append({
            "message": "Your pace is slow. Reduce hesitation pauses.",
            "tip_type": "pace",
            "start_sec": 0.0,
            "end_sec": min(duration_sec, 30.0),
        })

    return {
        "score_0_100": final_score,
        "label": label,
        "confidence": 0.8,
        "abstained": False,
        "details": {
            "overall_wpm": wpm,
            "mean_pause_sec": mean_pause,
            "pause_ratio": pause_ratio,
            "speech_ratio": speech_ratio,
            "rule_score": rule_score,
            "regressor_score": regressor_score,
            "segment_stats": compute_segment_wpm(words),
        },
        "feedback": feedback,
    }
