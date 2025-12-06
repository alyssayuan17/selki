"""
analyzer/audio_to_json.py

Core pipeline: audio file -> low-level JSON features.

Responsibilities:
- Load audio
- Run ASR (Whisper) to get word-level timestamps
- (Optionally) run VAD
- Extract simple audio features (duration, pitch, energy)
- Derive pause segments from word timings
- Return a JSON-serializable dict
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

import librosa
import whisper

from analyzer.utils.vad import run_vad, vad_to_silence_segments

# Set up logging
logger = logging.getLogger(__name__)


# -----------------------------
# Data structures
# -----------------------------

@dataclass
class WordTiming:
    start: float  # seconds
    end: float    # seconds
    text: str
    probability: Optional[float] = None  # Whisper avg prob, if available


@dataclass
class PauseSegment:
    start: float  # seconds
    end: float    # seconds
    duration: float  # seconds


@dataclass
class AudioFeatureSummary:
    sample_rate: int
    duration: float
    mean_pitch_hz: Optional[float]
    pitch_std_hz: Optional[float]
    mean_energy: float
    energy_std: float


# -----------------------------
# Public API
# -----------------------------

def audio_to_json(
    audio_path: str | Path,
    whisper_model_name: str = "small",
    target_sr: int = 16000,
    min_pause_s: float = 0.25,
    enable_vad: bool = True,
) -> Dict[str, Any]:
    """
    High-level pipeline:
      - load audio
      - run Whisper ASR with word timestamps
      - derive pauses
      - compute simple pitch/energy statistics
      - return JSON-serializable dict

    This function should be called by your FastAPI layer.

    Raises:
        ValueError: If audio file doesn't exist or is invalid
        RuntimeError: If audio processing fails
    """
    logger.info(f"Starting audio_to_json for: {audio_path}")

    # Validate input path
    audio_path = Path(audio_path)
    if not audio_path.exists():
        error_msg = f"Audio file not found: {audio_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not audio_path.is_file():
        error_msg = f"Path is not a file: {audio_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Check file extension
    valid_extensions = {'.wav', '.mp3', '.flac', '.m4a', '.ogg', '.opus'}
    if audio_path.suffix.lower() not in valid_extensions:
        logger.warning(f"Unusual audio file extension: {audio_path.suffix}. Proceeding anyway.")

    # 1) Load raw audio
    try:
        logger.debug(f"Loading audio with target_sr={target_sr}")
        y, sr = load_audio(audio_path, target_sr=target_sr)
        total_duration = len(y) / sr
        logger.info(f"Audio loaded: duration={total_duration:.2f}s, sr={sr}Hz, samples={len(y)}")

        if total_duration < 0.1:
            logger.warning(f"Audio is very short: {total_duration}s")
        if total_duration > 7200:  # 2 hours
            logger.warning(f"Audio is very long: {total_duration}s - processing may take a while")

    except Exception as e:
        error_msg = f"Failed to load audio file: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

    # 2) Run ASR to get word-level timings
    try:
        logger.debug(f"Running Whisper ASR with model={whisper_model_name}")
        words = run_whisper_word_timestamps(audio_path, model_name=whisper_model_name)
        logger.info(f"ASR completed: {len(words)} words detected")

        if len(words) == 0:
            logger.warning("No words detected by Whisper - audio may be silent or unintelligible")

    except Exception as e:
        error_msg = f"Whisper ASR failed: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

    # 3) Derive pause segments from word timings
    try:
        logger.debug(f"Deriving pauses (min_pause={min_pause_s}s)")
        word_pauses = derive_pauses_from_words(words, min_pause_s=min_pause_s)
        logger.debug(f"Found {len(word_pauses)} pauses")
    except Exception as e:
        error_msg = f"Failed to derive pauses: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

    # 4) Extract pitch & energy time series + aggregate stats
    try:
        logger.debug("Extracting pitch and energy features")
        pitch_hz, energy = extract_pitch_and_energy(y, sr)
        audio_summary = summarize_audio(pitch_hz, energy, sr, len(y))
        logger.debug(f"Features extracted: mean_pitch={audio_summary.mean_pitch_hz}, mean_energy={audio_summary.mean_energy}")
    except Exception as e:
        error_msg = f"Failed to extract audio features: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

    # 5) VAD Analysis
    speech_segments = None
    silence_segments = None

    if enable_vad:
        try:
            logger.debug("Running VAD analysis")
            speech_segments = run_vad(y, sr)  # List[(start,end)]
            silence_segments = vad_to_silence_segments(speech_segments, total_duration)
            logger.debug(f"VAD completed: {len(speech_segments) if speech_segments else 0} speech segments")
        except Exception as e:
            logger.warning(f"VAD analysis failed, continuing without it: {e}", exc_info=True)
            speech_segments = None
            silence_segments = None
    else:
        logger.debug("VAD disabled")

    # 6) Compute Noise and Mic Quality Heuristics (NEED TO FIX HOW THESE ARE CALCULATED)
    try:
        logger.debug("Computing noise summary")
        noise_summary = build_noise_summary(
            energy=energy,
            speech_segments=speech_segments,
            total_duration=total_duration,
            audio_summary=audio_summary,
        )
        logger.debug(f"Noise summary: mic_quality={noise_summary.get('mic_quality')}")
    except Exception as e:
        logger.warning(f"Failed to compute noise summary, using defaults: {e}", exc_info=True)
        noise_summary = {
            "avg_dbfs": -100.0,
            "noise_dbfs": -100.0,
            "speech_ratio": 0.0,
            "mic_quality": "unknown",
        }

    # 7) Build JSON-serializable dict
    return {
        "audio_metadata": {
            "sample_rate": audio_summary.sample_rate,
            "duration": audio_summary.duration,
        },
        "audio_features": {
            "mean_pitch_hz": audio_summary.mean_pitch_hz,
            "pitch_std_hz": audio_summary.pitch_std_hz,
            "mean_energy": audio_summary.mean_energy,
            "energy_std": audio_summary.energy_std,
        },
        "words": [
            {
                "start": w.start,
                "end": w.end,
                "text": w.text,
                "probability": w.probability,
            }
            for w in words
        ],
        "word_pauses": [
            {
                "start": p.start,
                "end": p.end,
                "duration": p.duration,
            }
            for p in word_pauses
        ],
        "vad_speech_segments": (
            [{"start": float(s), "end": float(e)} for (s, e) in speech_segments]
            if speech_segments
            else None
        ),
        "vad_silence_segments": (
            [{"start": float(s), "end": float(e)} for (s, e) in silence_segments]
            if silence_segments
            else None
        ),
        "noise_summary": noise_summary,
        # Raw timeseries for advanced metrics
        "raw_pitch_hz": pitch_hz.tolist() if pitch_hz is not None else None,
        # "raw_energy": energy.tolist(),  # Uncomment if needed
    }


# -----------------------------
# Low-level helpers
# -----------------------------

def load_audio(path: Path, target_sr: int = 16000) -> tuple[np.ndarray, int]:
    """
    Load audio as mono, resampled to target_sr.
    Returns (waveform, sample_rate).

    Raises:
        RuntimeError: If audio file cannot be loaded
    """
    try:
        # librosa returns float32 in [-1, 1]
        y, sr = librosa.load(path.as_posix(), sr=target_sr, mono=True)

        # Validate loaded audio
        if y is None or len(y) == 0:
            raise RuntimeError("Loaded audio is empty")

        if not np.isfinite(y).all():
            logger.warning("Audio contains non-finite values (inf/nan), attempting to clean")
            y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)

        return y, sr

    except Exception as e:
        error_msg = f"Failed to load audio from {path}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def run_whisper_word_timestamps(
    audio_path: Path,
    model_name: str = "small",
) -> List[WordTiming]:
    """
    Run Whisper ASR and return a list of WordTiming objects.
    Uses whisper's built-in word_timestamps.

    Raises:
        RuntimeError: If Whisper fails to load or transcribe
    """
    try:
        logger.debug(f"Loading Whisper model: {model_name}")
        model = whisper.load_model(model_name)
    except Exception as e:
        error_msg = f"Failed to load Whisper model '{model_name}': {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    try:
        # word_timestamps=True gives per-word timing info
        result = model.transcribe(
            audio_path.as_posix(),
            word_timestamps=True,
            verbose=False,
            temperature=0.0, # no sampling randomness i.e. fully deterministic
                             # could use 0.2 for "slightly more robust decoding in noisy conditions" ??? how does that make sense bruh

            # compression_ratio_threshold=2.4, # if a particular speech segment is too hard to decode (has score higher than 2.4), skip it
                                             # lower e.g. 2.0 = more aggressive skipping, higher e.g. 3.0 more tolerant of repetition/noise
            # logprob_threshold=-1.0, # skip segments with avg logprob below this (i.e. very low confidence)
                                    # e.g. -2 = more lenient, -0.5 = more aggressive skipping
            #  no_speech_threshold=0.4, # no-speech prob threshold to skip segment
                                     # lower = more aggressive skipping, higher = more tolerant
        )
    except Exception as e:
        error_msg = f"Whisper transcription failed: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    if not isinstance(result, dict):
        error_msg = f"Unexpected Whisper result type: {type(result)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    words: List[WordTiming] = []

    # Whisper result["segments"] each contain "words"
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            # 1. Require mandatory fields
            if "start" not in w or "end" not in w or "word" not in w:
                continue

            # Skip low-confidence words (GET RID OF GARBAGE HALLUCINATIONS)
            prob = w.get("probability", None)
            if prob is not None and prob < 0.2:
                continue

            # Skip very short tokens (likely punctuation/artifacts)
            if w["end"] - w["start"] < 0.03:
                    continue

            text = w["word"].strip() #.strip(" ,.!?;:-\"'()[]{}") IF WANT TO ELIMINATE PUNCTUATION

            # 2. Skip empty or garbage tokens
            if not text:
                continue

            # 3. Deduplicate tokens with same timestamps
            if words and abs(words[-1].start - float(w["start"])) < 0.01:
                continue

            words.append(
                WordTiming(
                    start=float(w["start"]),
                    end=float(w["end"]),
                    text=text,
                    probability=float(w.get("probability")) if "probability" in w else None,
                )
            )

    # If word_timestamps is missing (e.g., older Whisper), you could fall back to segment-level timings.

    return words


def derive_pauses_from_words(
    words: List[WordTiming],
    min_pause_s: float = 0.25,
) -> List[PauseSegment]:
    """
    Given sorted words, derive "silent" gaps between them as pauses.
    A pause is recorded if the gap between word_i.end and word_(i+1).start
    is at least min_pause_s seconds.
    """
    pauses: List[PauseSegment] = []

    if not words:
        return pauses

    # Ensure words are sorted by start time
    words_sorted = sorted(words, key=lambda w: w.start)

    for prev, nxt in zip(words_sorted, words_sorted[1:]):
        gap = nxt.start - prev.end
        if gap >= min_pause_s:
            pauses.append(
                PauseSegment(
                    start=prev.end,
                    end=nxt.start,
                    duration=gap,
                )
            )

    return pauses


def extract_pitch_and_energy(
    y: np.ndarray,
    sr: int,
    frame_length: int = 1024,
    hop_length: int = 256,
) -> tuple[Optional[np.ndarray], np.ndarray]:
    """
    Basic extraction of pitch (F0) and frame-wise energy.

    Pitch: uses librosa.yin (monophonic F0 estimation).
    Energy: frame-wise RMS.

    Returns (pitch_hz, energy), where pitch_hz can be None if extraction fails.
    """
    # Energy (RMS) per frame
    energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

    # Pitch using YIN, constrained to human speech range (roughly 50–500 Hz)
    try:
        pitch_hz = librosa.yin(
            y=y,
            fmin=50,
            fmax=500,
            sr=sr,
            frame_length=frame_length,
            hop_length=hop_length,
        )
    except Exception:
        # In case YIN fails (very short audio, silence, etc.)
        pitch_hz = None

    return pitch_hz, energy


def summarize_audio(
    pitch_hz: Optional[np.ndarray],
    energy: np.ndarray,
    sr: int,
    num_samples: int,
) -> AudioFeatureSummary:
    """
    Aggregate low-level features into a compact summary.
    """
    duration = num_samples / float(sr)

    if pitch_hz is not None:
        # Filter out unvoiced frames: YIN uses np.nan for unvoiced
        voiced = pitch_hz[~np.isnan(pitch_hz)]
        if len(voiced) > 0:
            mean_pitch = float(np.mean(voiced))
            pitch_std = float(np.std(voiced))
        else:
            mean_pitch = None
            pitch_std = None
    else:
        mean_pitch = None
        pitch_std = None

    mean_energy = float(np.mean(energy)) if energy.size > 0 else 0.0
    energy_std = float(np.std(energy)) if energy.size > 0 else 0.0

    return AudioFeatureSummary(
        sample_rate=sr,
        duration=duration,
        mean_pitch_hz=mean_pitch,
        pitch_std_hz=pitch_std,
        mean_energy=mean_energy,
        energy_std=energy_std,
    )

# ================================
# Noise & mic-quality heuristics
# ================================

def build_noise_summary(
    energy: np.ndarray,
    speech_segments: Optional[List[tuple]],
    total_duration: float,
    audio_summary: AudioFeatureSummary,
) -> Dict[str, Any]:
    """
    Produce a structured noise summary block expected by run_pipeline:
      {
        "avg_dbfs": float,
        "noise_dbfs": float,
        "speech_ratio": float,
        "mic_quality": str,
      }

    This is *heuristic*. Replace later with real DSP/spectral noise estimation.
    """
    # ------ 1) Convert RMS energy to dBFS-like scale ------
    # RMS energy is 0..something small. Convert to dB.
    avg_rms = float(np.mean(energy)) if len(energy) > 0 else 0.0
    if avg_rms <= 1e-12:
        avg_dbfs = -100.0
    else:
        avg_dbfs = 20 * np.log10(avg_rms)

    # Noise estimate = bottom 20% energy frames
    bottom = np.percentile(energy, 20) if len(energy) > 0 else 0.0
    if bottom <= 1e-12:
        noise_dbfs = -100.0
    else:
        noise_dbfs = 20 * np.log10(bottom)

    # ------ 2) Speech ratio from VAD ------
    if speech_segments:
        speech_total = sum(e - s for (s, e) in speech_segments)
        speech_ratio = speech_total / max(total_duration, 1e-6)
    else:
        speech_ratio = 0.0

    # ------ 3) Mic quality heuristic ------
    if audio_summary.mean_energy < 0.001:
        mic_quality = "very_quiet"
    elif noise_dbfs > -30:
        mic_quality = "noisy"
    else:
        mic_quality = "ok"

    return {
        "avg_dbfs": float(avg_dbfs),
        "noise_dbfs": float(noise_dbfs),
        "speech_ratio": float(speech_ratio),
        "mic_quality": mic_quality,
    }


# -----------------------------
# CLI helper for manual testing
# -----------------------------

if __name__ == "__main__":
    """
    Allow running:

        python -m analyzer.audio_to_json path/to/audio.wav

    and print the JSON to stdout for quick debugging.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run audio -> JSON feature pipeline.")
    parser.add_argument("audio_path", type=str, help="Path to an audio file (wav/mp3/etc.)")
    parser.add_argument("--model", type=str, default="small", help="Whisper model name")
    args = parser.parse_args()

    result = audio_to_json(args.audio_path, whisper_model_name=args.model)
    print(json.dumps(result, indent=2))


