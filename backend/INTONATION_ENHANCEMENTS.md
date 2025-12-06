# Intonation Metric Enhancements

## Summary

The intonation metric has been enhanced with **Phase 1 improvements** from the recommendations in [intonation_improvements.md](intonation_improvements.md), adding three key factors that make the classification more accurate and speaker-independent.

## What Was Added

### 1. **Pitch Range (pitch_range_hz)**

**What it is**: The estimated range of pitch variation (max - min F0)

**How it's calculated**:
```python
pitch_range_hz ≈ 4 * pitch_std_hz
```

This is a statistical estimate assuming normal distribution (4σ covers ~95% of values). While not as precise as computing from raw pitch data, it's a good approximation.

**Why it matters**: Pitch range is different from standard deviation. A speaker can have:
- High std but small range (frequent small variations)
- Low std but large range (occasional large jumps)

**Thresholds**:
- < 50 Hz → monotone (less than half octave)
- 50-100 Hz → moderate (less than 1 octave)
- \> 100 Hz → dynamic (more than 1 octave)

### 2. **Coefficient of Variation (pitch_cov)**

**What it is**: Normalized pitch variance = std / mean

**Formula**:
```python
pitch_cov = pitch_std_hz / mean_pitch_hz
```

**Why it matters**: Makes the metric **speaker-independent**. Male speakers (mean ~120 Hz) and female speakers (mean ~210 Hz) have different absolute pitch values, but similar relative variation.

**Example**:
- Male speaker: std = 18 Hz, mean = 120 Hz → CoV = 0.15 (moderate)
- Female speaker: std = 30 Hz, mean = 200 Hz → CoV = 0.15 (moderate)

Both have the same **relative** variation, even though absolute std is different!

**Thresholds**:
- < 0.10 → monotone
- 0.10-0.20 → moderate variation
- \> 0.20 → dynamic

### 3. **Multi-Factor Classification**

Instead of using only `pitch_std_hz`, the new system combines:
- **pitch_std_hz** (35% weight) - Variance is most important
- **pitch_range_hz** (25% weight) - Range is important
- **pitch_cov** (25% weight) - CoV is speaker-independent
- **energy_std** (15% weight) - Energy is supplementary

Each factor is scored 0-2 (monotone/moderate/dynamic), then weighted and combined into a total score:

```python
total_score = (
    0.35 * pitch_std_score +    # Variance is important
    0.25 * pitch_range_score +  # Range is important
    0.25 * cov_score +           # CoV is speaker-independent
    0.15 * energy_score          # Energy is supplementary
)

# total_score < 0.7 → monotone
# 0.7 ≤ total_score < 1.4 → somewhat_monotone
# total_score ≥ 1.4 → dynamic
```

This multi-factor approach is more robust than relying on a single metric.

### 4. **Enhanced Feedback with Actual Values**

Feedback messages now show the actual measured values to make them more actionable:

**Before**:
> "Your pitch and loudness stay relatively flat, which can sound monotone."

**After**:
> "Your pitch stays relatively flat (variation: 8.2 Hz, range: 33 Hz). Try varying your pitch by at least 100-150 Hz (about 1 octave) to sound more engaging. Emphasize key words with pitch rises."

## Updated Schema

The metric now returns additional details:

```json
{
  "score_0_100": 45,
  "label": "monotone",
  "confidence": 0.65,
  "abstained": false,
  "details": {
    "mean_pitch_hz": 150.0,
    "pitch_std_hz": 8.0,
    "pitch_range_hz": 32.0,        // NEW: estimated range
    "pitch_cov": 0.053,             // NEW: coefficient of variation
    "energy_mean": 0.05,            // NEW: mean energy
    "energy_std": 0.003,
    "prosody_variance_score": 0.127
  },
  "feedback": [...]
}
```

## Testing

The enhanced metric is tested in [test_intonation.py](test_intonation.py) with:

1. **Unit tests**: Synthetic data covering monotone, somewhat_monotone, dynamic, and abstention cases
2. **Assertions**: Verify that pitch_range_hz and pitch_cov are computed correctly
3. **Integration test**: Real audio file processing

Run tests with:
```bash
cd backend
python test_intonation.py
```

## Future Enhancements (Phase 2 & 3)

### Phase 2 - Better Thresholds
- Tune thresholds based on real test data
- Add gender/speaker normalization
- Calibrate weights in multi-factor scoring

### Phase 3 - Advanced Features
- **Temporal analysis**: Pitch change rate (changes per second)
  - Distinguishes slow drift (monotone-sounding) from frequent changes (dynamic)
- **Raw pitch data**: Compute exact pitch_range from raw F0 timeseries
  - Currently using estimated range (4σ approximation)
  - Actual range would be more accurate: `max(voiced_pitch) - min(voiced_pitch)`

See [intonation_improvements.md](intonation_improvements.md) for full implementation details.

## Performance

- **No performance impact**: All calculations use existing summary statistics
- **Backward compatible**: Existing code continues to work unchanged
- **Confidence boost**: +0.05 to confidence when all factors are available

## References

- **Pitch Range**: 1 octave = 2x frequency = 100 Hz for male (100→200 Hz), 200 Hz for female (200→400 Hz)
- **CoV Research**: Professional speakers typically have CoV = 0.15-0.25
- **Multi-factor Classification**: Based on prosody research combining multiple acoustic features
