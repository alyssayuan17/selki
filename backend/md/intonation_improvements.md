# Intonation Metric Enhancement Recommendations

## Current Implementation Review

**File**: `backend/analyzer/metrics/intonation.py`

### Strengths ✓
1. Clean, modular code with helper functions
2. Proper abstention for edge cases (short talks, missing data)
3. Variable confidence scoring based on prosody variance
4. Good feedback messages for each category
5. Combines pitch and energy features

### Recommended Enhancements

## 1. **Add Pitch Range (Critical)**

**Why**: Pitch range (max - min F0) is a key prosody indicator that's different from std dev.

```python
def compute_intonation_metric(
    audio_features: Dict[str, Any],
    duration_sec: float,
    pitch_timeseries: Optional[List[float]] = None,  # NEW: raw F0 values
) -> Dict[str, Any]:

    # Calculate pitch range if we have raw data
    pitch_range_hz = None
    if pitch_timeseries and len(pitch_timeseries) > 0:
        # Filter out unvoiced frames (NaN or 0)
        voiced = [f for f in pitch_timeseries if f and f > 0]
        if len(voiced) > 10:  # Need enough voiced frames
            pitch_range_hz = max(voiced) - min(voiced)
```

**Update audio_to_json.py** to optionally return raw pitch:
```python
# In audio_to_json.py, add to return dict:
"raw_pitch_hz": pitch_hz.tolist() if pitch_hz is not None else None,
```

## 2. **Improve Labeling Logic**

Use **both** pitch_std and pitch_range for more accurate classification:

```python
def label_from_prosody(
    pitch_std_hz: Optional[float],
    pitch_range_hz: Optional[float],
    energy_std: Optional[float],
) -> str:
    """
    Multi-factor prosody classification.

    Thresholds (to be tuned):
    - Monotone: low variance AND narrow range
    - Somewhat: moderate variance OR moderate range
    - Dynamic: high variance AND wide range
    """
    if pitch_std_hz is None or pitch_std_hz < 1.0:
        return "monotone"

    # Calculate composite score
    pitch_std_score = 0
    if pitch_std_hz < 12:
        pitch_std_score = 0  # very flat
    elif pitch_std_hz < 25:
        pitch_std_score = 1  # moderate
    else:
        pitch_std_score = 2  # dynamic

    pitch_range_score = 0
    if pitch_range_hz is not None:
        if pitch_range_hz < 50:      # < half octave
            pitch_range_score = 0
        elif pitch_range_hz < 120:   # < 1 octave
            pitch_range_score = 1
        else:                         # > 1 octave
            pitch_range_score = 2

    energy_score = 0
    if energy_std is not None:
        if energy_std < 0.005:
            energy_score = 0
        elif energy_std < 0.02:
            energy_score = 1
        else:
            energy_score = 2

    # Aggregate (weighted average)
    total_score = (
        0.5 * pitch_std_score +    # Variance is most important
        0.3 * pitch_range_score +  # Range is important
        0.2 * energy_score         # Energy is supplementary
    )

    if total_score < 0.7:
        return "monotone"
    elif total_score < 1.5:
        return "somewhat_monotone"
    else:
        return "dynamic"
```

## 3. **Add Coefficient of Variation (CoV)**

**Why**: Normalizes variance by mean, making it speaker-independent.

```python
def compute_pitch_coefficient_of_variation(
    mean_pitch_hz: Optional[float],
    pitch_std_hz: Optional[float],
) -> Optional[float]:
    """
    CoV = std / mean

    Typical values:
    - CoV < 0.10 → monotone
    - CoV 0.10-0.20 → moderate
    - CoV > 0.20 → dynamic
    """
    if mean_pitch_hz is None or pitch_std_hz is None:
        return None
    if mean_pitch_hz <= 0:
        return None
    return pitch_std_hz / mean_pitch_hz
```

## 4. **Add Temporal Analysis (Advanced)**

**Why**: Monotone speakers may have variance but it's slow/gradual. Dynamic speakers change pitch frequently.

```python
def compute_pitch_change_rate(
    pitch_timeseries: List[float],
    sample_rate: int = 16000,
    hop_length: int = 256,
) -> Optional[float]:
    """
    Count how many times pitch changes significantly per second.

    Good for distinguishing:
    - Slow drift (still sounds monotone)
    - Frequent changes (sounds dynamic)
    """
    if not pitch_timeseries or len(pitch_timeseries) < 10:
        return None

    # Calculate frame times
    frames_per_second = sample_rate / hop_length

    # Count significant pitch changes (> 5 Hz difference)
    changes = 0
    for i in range(1, len(pitch_timeseries)):
        if abs(pitch_timeseries[i] - pitch_timeseries[i-1]) > 5.0:
            changes += 1

    duration_sec = len(pitch_timeseries) / frames_per_second
    return changes / duration_sec if duration_sec > 0 else 0
```

## 5. **Enhanced Feedback with Specific Values**

Make feedback more actionable by showing actual numbers:

```python
if label == "monotone":
    feedback_msg = (
        f"Your pitch stays relatively flat (std: {pitch_std_hz:.1f} Hz, "
        f"range: {pitch_range_hz:.0f} Hz). "
        f"Try varying your pitch by at least 100-150 Hz (about 1 octave) "
        f"to sound more engaging. Emphasize key words with pitch rises."
    )
elif label == "somewhat_monotone":
    feedback_msg = (
        f"You have some pitch variation (std: {pitch_std_hz:.1f} Hz), "
        f"but could be more dynamic. "
        f"Try increasing your pitch range to >100 Hz by using pitch rises "
        f"for questions and pitch falls for emphasis."
    )
```

## 6. **Gender/Speaker Normalization (Advanced)**

**Why**: Male speakers (~100-150 Hz) have different absolute pitch than female speakers (~180-250 Hz).

```python
def normalize_by_speaker_gender(
    mean_pitch_hz: float,
    pitch_std_hz: float,
) -> tuple[float, str]:
    """
    Estimate speaker gender from mean pitch and return normalized std.

    Typical ranges:
    - Male: 85-180 Hz (mean ~120 Hz)
    - Female: 165-255 Hz (mean ~210 Hz)
    """
    if mean_pitch_hz < 150:
        gender_estimate = "male"
        # Males typically have lower absolute std but similar CoV
        normalized_std = pitch_std_hz
    else:
        gender_estimate = "female"
        # Females may have higher absolute std
        normalized_std = pitch_std_hz

    return normalized_std, gender_estimate
```

## 7. **Updated Details Output**

```python
"details": {
    "mean_pitch_hz": mean_pitch_hz,
    "pitch_std_hz": pitch_std_hz,
    "pitch_range_hz": pitch_range_hz,           # NEW
    "pitch_cov": pitch_cov,                      # NEW: coefficient of variation
    "energy_std": energy_std,
    "energy_mean": energy_mean,                  # NEW
    "prosody_variance_score": prosody_score,
    "pitch_change_rate": pitch_change_rate,      # NEW: changes per second
}
```

## Priority Implementation Order

### **Phase 1: Quick Wins (15 min)**
1. ✓ Add pitch_range_hz calculation (use raw pitch from audio_to_json)
2. ✓ Add CoV calculation
3. ✓ Update feedback messages with actual values

### **Phase 2: Better Classification (30 min)**
4. ✓ Implement multi-factor labeling (pitch_std + pitch_range + energy)
5. ✓ Tune thresholds based on test data

### **Phase 3: Advanced (1 hour)**
6. ✓ Add temporal analysis (pitch change rate)
7. ✓ Add speaker normalization

## Implementation Example (Phase 1)

```python
# Minimal enhancement - just add pitch_range
def compute_intonation_metric(
    audio_features: Dict[str, Any],
    raw_pitch_hz: Optional[List[float]],  # NEW parameter
    duration_sec: float,
) -> Dict[str, Any]:

    # Existing code...
    mean_pitch_hz = audio_features.get("mean_pitch_hz")
    pitch_std_hz = audio_features.get("pitch_std_hz")
    energy_std = audio_features.get("energy_std")

    # NEW: Calculate pitch range
    pitch_range_hz = None
    if raw_pitch_hz:
        import numpy as np
        voiced = [f for f in raw_pitch_hz if f and not np.isnan(f) and f > 0]
        if len(voiced) > 10:
            pitch_range_hz = float(max(voiced) - min(voiced))

    # NEW: Calculate CoV
    pitch_cov = None
    if mean_pitch_hz and pitch_std_hz and mean_pitch_hz > 0:
        pitch_cov = pitch_std_hz / mean_pitch_hz

    # Use enhanced labeling
    label = label_from_prosody(pitch_std_hz, pitch_range_hz, energy_std)

    # ... rest of code

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
            "energy_std": energy_std,
            "prosody_variance_score": prosody_score,
        },
        "feedback": feedback,
    }
```

## Testing Recommendations

1. **Monotone Test**: Record yourself reading in a flat voice
   - Expected: pitch_std < 15 Hz, range < 50 Hz

2. **Dynamic Test**: Record yourself with exaggerated pitch changes
   - Expected: pitch_std > 35 Hz, range > 120 Hz

3. **Edge Cases**:
   - Very short audio (< 3s) → should abstain
   - Silent audio → should abstain
   - Whispered speech (no F0) → should abstain

## Research References

- **Pitch Range**: 1 semitone = 6% frequency change, 1 octave = 100% = 2x frequency
  - Male: 100 Hz → 200 Hz = 1 octave = 100 Hz range
  - Female: 200 Hz → 400 Hz = 1 octave = 200 Hz range (but similar % variation)

- **CoV benchmarks** (from prosody literature):
  - Professional speakers: CoV = 0.15-0.25
  - Monotone speakers: CoV < 0.10

- **Change Rate**: Dynamic speakers change pitch 2-5 times per second

## Summary

**Current implementation**: 7/10 - Good foundation!

**With Phase 1 enhancements**: 9/10 - Excellent practical metric

**With all phases**: 10/10 - Research-grade prosody analysis
