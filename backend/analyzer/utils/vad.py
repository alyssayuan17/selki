"""
utils/vad.py

Simple Voice Activity Detection wrapper using Silero VAD.
Produces speech segments as (start_sec, end_sec).
"""

from __future__ import annotations
from typing import List, Tuple
import torch
import numpy as np

# Load Silero model once (heavy op)
_model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    force_reload=False
)

(get_speech_timestamps,
 get_speech_prob,
 get_silero_audio,
 VADIterator,
 collect_chunks) = utils


def run_vad(
    y: np.ndarray,
    sr: int,
    min_speech_ms: int = 150,
    min_silence_ms: int = 100,
) -> List[Tuple[float, float]]:
    """
    Run Silero VAD on waveform y (float32, mono).
    Returns list of (start_sec, end_sec) speech segments.

    We return *when voice is detected*, NOT silence.
    This lets audio_to_json optionally compute pauses from either:
      - word gaps (ASR)
      - silence gaps (VAD)
    """

    # Convert numpy waveform → PyTorch tensor
    audio_t = torch.from_numpy(y).float().cpu()

    # Silero expects 16k audio
    # (your pipeline already resamples y to 16k)
    speech_ts = get_speech_timestamps(
        audio_t,
        _model,
        sampling_rate=sr,
        min_speech_duration_ms=min_speech_ms,
        min_silence_duration_ms=min_silence_ms,
    )

    output = []
    for seg in speech_ts:
        start = seg["start"] / sr
        end = seg["end"] / sr
        output.append((start, end))

    return output

def vad_to_silence_segments(
    vad_segments: List[Tuple[float, float]],
    total_duration: float,
    min_silence_s: float = 0.15,
) -> List[Tuple[float, float]]:
    """
    Convert VAD speech segments -> silence segments.
    Speech = voice detected.
    Silence = gaps between speech segments.

    Example:
    Speech: [(1.0, 2.0), (3.0, 4.0)]
    Duration = 5 sec
    Silence = [(0,1), (2,3), (4,5)]
    """

    if not vad_segments:
        return [(0.0, float(total_duration))]

    output = []
    vad_sorted = sorted(vad_segments, key=lambda x: x[0])

    # Before first speech
    first_start = vad_sorted[0][0]
    if first_start > min_silence_s:
        output.append((0.0, first_start))

    # Between speech segments
    for (s1, e1), (s2, e2) in zip(vad_sorted, vad_sorted[1:]):
        gap_start = e1
        gap_end = s2
        if (gap_end - gap_start) >= min_silence_s:
            output.append((gap_start, gap_end))

    # After last speech
    last_end = vad_sorted[-1][1]
    if total_duration - last_end >= min_silence_s:
        output.append((last_end, float(total_duration)))

    return output
