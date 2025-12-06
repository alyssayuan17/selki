# Pitch Range Outlier Filtering Fix

## Problem

The exact pitch range calculation was producing unrealistically large values due to **pitch tracking errors** in librosa's YIN algorithm.

### Example from test.wav

```
Raw pitch values: [50.0, 56.2, 500.0, 55.6, 55.6, 61.3, ...]
                              ^^^^
                              outlier!

Raw range: max - min = 500 - 50 = 450 Hz
```

**Issue**: The 500 Hz value is a spurious octave jump (pitch tracking error), not actual speech.

## Root Cause

Pitch tracking algorithms like YIN occasionally produce:
- **Octave jumps**: F0 detected at 2× or 0.5× the actual pitch
- **Noise-induced false detections**: Background noise interpreted as very high/low pitch
- **Harmonics misidentified as F0**: Higher harmonics detected instead of fundamental

These outliers shouldn't be included in the pitch range calculation.

## Solution

Use **percentile-based filtering** instead of raw min/max:

```python
# Before (problematic):
pitch_range = float(np.max(voiced) - np.min(voiced))  # 450 Hz with outliers

# After (robust):
p5 = np.percentile(voiced, 5)   # 5th percentile
p95 = np.percentile(voiced, 95)  # 95th percentile
pitch_range = float(p95 - p5)    # 165 Hz without outliers
```

### Why 5th-95th percentile?

- **5th percentile**: Excludes bottom 5% of values (low-pitch errors)
- **95th percentile**: Excludes top 5% of values (high-pitch errors)
- **90% coverage**: Captures the true pitch range used 90% of the time
- **Robust**: Standard approach in speech prosody research

## Results

### test.wav analysis

| Method | Min | Max | Range | Notes |
|--------|-----|-----|-------|-------|
| **Before** (raw min/max) | 50 Hz | 500 Hz | 450 Hz | Unrealistic! |
| **After** (5th-95th %ile) | 51 Hz | 216 Hz | 165 Hz | Realistic ✓ |

### Comparison to statistical estimate

- **Exact range (percentile-based)**: 165 Hz
- **Statistical estimate (4σ)**: 306 Hz
- **Difference**: Exact method is more accurate when outliers are filtered

## Implementation

File: [intonation.py](analyzer/metrics/intonation.py)

```python
def compute_exact_pitch_range(raw_pitch_hz: Optional[list]) -> Optional[float]:
    """
    Compute exact pitch range from raw pitch timeseries.

    Note:
        Uses 5th-95th percentile to exclude outliers from pitch tracking errors.
        Raw F0 from librosa.yin can have spurious octave jumps or noise-induced
        false detections that should be filtered out.
    """
    if raw_pitch_hz is None or len(raw_pitch_hz) == 0:
        return None

    import numpy as np
    pitch_array = np.array(raw_pitch_hz)
    voiced = pitch_array[~np.isnan(pitch_array) & (pitch_array > 0)]

    if len(voiced) < 10:
        return None

    # Use percentiles to exclude outliers (5th-95th percentile)
    p5 = np.percentile(voiced, 5)
    p95 = np.percentile(voiced, 95)
    pitch_range = float(p95 - p5)
    return pitch_range
```

## Impact

✓ More realistic pitch ranges
✓ Robust to pitch tracking errors
✓ Consistent with speech prosody research methods
✓ Prevents misleading feedback ("your range is 450 Hz!" → "your range is 165 Hz")

## Testing

```bash
cd backend
python test_intonation.py
```

All tests passing with realistic pitch ranges.

## Alternative Approaches Considered

1. **IQR (Interquartile Range)**: Q1-Q3 (25th-75th percentile)
   - Too conservative, would miss actual pitch excursions
   - Not used

2. **3-sigma clipping**: mean ± 3*std
   - Assumes normal distribution (pitch is often not)
   - Not used

3. **Median Absolute Deviation (MAD)**
   - More complex, similar results
   - Not needed for this use case

## References

- **Speech Prosody Research**: 5th-95th percentile is standard for F0 range
- **Librosa YIN**: Known to have octave errors, requires post-filtering
- **Praat (speech analysis tool)**: Uses similar percentile-based pitch range
