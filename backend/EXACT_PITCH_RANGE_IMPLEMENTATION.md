# Exact Pitch Range Implementation

## Summary

Enhanced the intonation metric to compute **exact pitch range** from raw F0 timeseries instead of relying solely on statistical estimation.

## What Was Changed

### 1. **audio_to_json.py** - Export Raw Pitch Data

**Line 235**: Uncommented raw pitch output
```python
"raw_pitch_hz": pitch_hz.tolist() if pitch_hz is not None else None,
```

**Why**: The raw F0 timeseries was already being computed by `extract_pitch_and_energy()` using librosa.yin, but wasn't being returned in the JSON output. Now it's available for downstream metrics.

### 2. **run_pipeline.py** - Pass Raw Data to Intonation Metric

**Lines 387-390**: Extract and pass raw_pitch_hz
```python
raw_pitch_hz = audio_json.get("raw_pitch_hz")  # NEW: pass raw pitch for exact range
metrics["intonation"] = compute_intonation_metric(
    audio_features, duration_sec, raw_pitch_hz=raw_pitch_hz
)
```

**Why**: The intonation metric now receives the raw timeseries data for exact range calculation.

### 3. **intonation.py** - Exact Range Calculation

#### Added `compute_exact_pitch_range()` function (lines 46-68)

```python
def compute_exact_pitch_range(raw_pitch_hz: Optional[list]) -> Optional[float]:
    """
    Compute exact pitch range from raw pitch timeseries.

    Args:
        raw_pitch_hz: List of F0 values per frame (NaN for unvoiced frames)

    Returns:
        Exact pitch range (max - min) in Hz, or None if no valid data
    """
    if raw_pitch_hz is None or len(raw_pitch_hz) == 0:
        return None

    # Filter out unvoiced frames (NaN or zero values)
    import numpy as np
    pitch_array = np.array(raw_pitch_hz)
    voiced = pitch_array[~np.isnan(pitch_array) & (pitch_array > 0)]

    if len(voiced) < 10:  # Need at least 10 voiced frames
        return None

    pitch_range = float(np.max(voiced) - np.min(voiced))
    return pitch_range
```

**Key features**:
- Filters out unvoiced frames (NaN and zero values)
- Requires at least 10 voiced frames for robust calculation
- Returns exact max - min range in Hz

#### Updated `compute_intonation_metric()` (line 248)

**New parameter**:
```python
def compute_intonation_metric(
    audio_features: Dict[str, Any],
    duration_sec: float,
    raw_pitch_hz: Optional[list] = None,  # NEW parameter
) -> Dict[str, Any]:
```

**Fallback logic** (lines 300-303):
```python
# Try to compute exact pitch range from raw data first, fall back to estimate
pitch_range_hz = compute_exact_pitch_range(raw_pitch_hz)
if pitch_range_hz is None:
    # Fallback to statistical estimate
    pitch_range_hz = estimate_pitch_range(mean_pitch_hz, pitch_std_hz)
```

**Visual indicator** (lines 330-331):
```python
has_exact_range = compute_exact_pitch_range(raw_pitch_hz) is not None
range_qualifier = "" if has_exact_range else "~"  # ~ indicates estimate
```

**Enhanced feedback** (e.g., line 335):
```python
pitch_range_str = f"{range_qualifier}{pitch_range_hz:.0f} Hz"
# Results in: "150 Hz" (exact) or "~150 Hz" (estimated)
```

## How It Works

### Data Flow

1. **audio_to_json.py** extracts raw F0 using librosa.yin (~62.5 Hz frame rate with 256 hop_length @ 16kHz)
2. **audio_to_json.py** returns raw_pitch_hz as list of floats (NaN for unvoiced frames)
3. **run_pipeline.py** passes raw_pitch_hz to intonation metric
4. **intonation.py** attempts exact range calculation:
   - Filters out NaN and zero values (unvoiced frames)
   - Computes max - min from remaining voiced frames
   - Falls back to statistical estimate (4σ) if insufficient data
5. **Feedback messages** indicate exact ("150 Hz") vs estimated ("~150 Hz") ranges

### Exact vs Estimated Range

| Method | Calculation | Accuracy | When Used |
|--------|-------------|----------|-----------|
| **Exact** | `max(voiced_F0) - min(voiced_F0)` | Precise | When raw_pitch_hz available and ≥10 voiced frames |
| **Estimated** | `4 * pitch_std_hz` | ~95% coverage approximation | Fallback when raw data unavailable |

**Example comparison**:
- Speaker with mean=150 Hz, std=20 Hz
- **Estimated range**: 4 × 20 = 80 Hz (assuming normal distribution)
- **Exact range**: Could be 95 Hz (if actual max=198, min=103)
- The exact method captures the true range without statistical assumptions

## Benefits

1. **More accurate**: Captures actual pitch excursions, not just variance
2. **Robust**: Falls back gracefully when raw data unavailable
3. **Transparent**: Visual indicator shows users when estimate is used
4. **No breaking changes**: Optional parameter, backward compatible

## Testing

Run the test suite to verify:
```bash
cd backend
python test_intonation.py
```

**Expected behavior**:
- Unit tests should pass (using synthetic data, will use estimated range)
- Integration test with real audio will use exact range (if audio has voiced speech)
- Feedback messages will show "~" prefix only when falling back to estimate

## Performance Impact

**Negligible**:
- Raw pitch is already computed by audio_to_json.py
- Exact range calculation is O(n) where n = number of frames (~1000 for 16s audio)
- NumPy array operations are highly optimized

## Future Enhancements

From [intonation_improvements.md](intonation_improvements.md), remaining Phase 3 items:

- **Temporal analysis**: Pitch change rate (changes per second) to distinguish slow drift from frequent changes
- **Speaker normalization**: Adjust thresholds based on estimated gender/speaker characteristics

## References

- **Pitch Range**: 1 octave = 2× frequency = ~100 Hz for male, ~200 Hz for female
- **Librosa F0**: Uses YIN algorithm with configurable fmin/fmax
- **Voiced frames**: Detected by F0 tracker, NaN indicates unvoiced/silent segments
