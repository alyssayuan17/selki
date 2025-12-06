from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .audio_to_json import audio_to_json
from analyzer.metrics.pace import compute_pace_metric
from analyzer.metrics.pause_quality import compute_pause_quality_metric
from analyzer.metrics.fillers import compute_fillers_metric
from analyzer.metrics.intonation import compute_intonation_metric

# Set up logging
logger = logging.getLogger(__name__)


# ---- Small helpers / types -------------------------------------------------


@dataclass
class PresentationJobInput:
    """
    Typed view of the POST /api/v1/presentations request payload.

    This mirrors your agreed JSON request format, but we keep it
    as a simple dataclass so the analyzer layer is independent
    from FastAPI / Pydantic.
    """
    audio_url: str
    video_url: Optional[str]
    language: str
    talk_type: str
    audience_type: str
    requested_metrics: List[str]
    user_metadata: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PresentationJobInput":
        return cls(
            audio_url=data["audio_url"],
            video_url=data.get("video_url"),
            language=data.get("language", "en"),
            talk_type=data.get("talk_type", "unspecified"),
            audience_type=data.get("audience_type", "general"),
            requested_metrics=list(data.get("requested_metrics", [])),
            user_metadata=dict(data.get("user_metadata", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audio_url": self.audio_url,
            "video_url": self.video_url,
            "language": self.language,
            "talk_type": self.talk_type,
            "audience_type": self.audience_type,
            "requested_metrics": self.requested_metrics,
            "user_metadata": self.user_metadata,
        }


# ---- Helper functions to build parts of the final JSON ---------------------


def _build_transcript_from_words(words: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build the transcript block used in:
      - GET /api/v1/presentations/{job_id}/full
      - GET /api/v1/presentations/{job_id}/transcript

    For now this is a very simple version:
      - full_text is just the concatenation of word texts
      - segments is a single segment over the whole audio
      - tokens are word-level tokens with is_filler=False
    """
    if not words:
        return {
            "full_text": "",
            "language": "en",
            "segments": [],
            "tokens": [],
        }

    cleaned_words = [w for w in words if isinstance(w, dict) and w.get("text")]
    full_text = " ".join(
        w["text"].strip() for w in cleaned_words if isinstance(w.get("text"), str)
    )

    # Get overall min/max times and simple average confidence
    start_times = [w.get("start") for w in cleaned_words if "start" in w]
    end_times = [w.get("end") for w in cleaned_words if "end" in w]
    probs = [w.get("probability") for w in cleaned_words if "probability" in w]

    if start_times and end_times:
        overall_start = float(min(start_times))
        overall_end = float(max(end_times))
    else:
        overall_start = 0.0
        overall_end = 0.0

    avg_conf = float(sum(p for p in probs if p is not None) / len(probs)) if probs else 0.0

    segments = [
        {
            "start_sec": overall_start,
            "end_sec": overall_end,
            "text": full_text,
            "avg_confidence": avg_conf,
        }
    ]

    tokens = []
    for w in cleaned_words:
        tokens.append(
            {
                "text": w["text"].strip(),
                "start_sec": float(w.get("start", 0.0)),
                "end_sec": float(w.get("end", 0.0)),
                # TODO: later wire in filler detection here
                "is_filler": False,
            }
        )

    return {
        "full_text": full_text,
        "language": "en",  # you can override this with detected language later
        "segments": segments,
        "tokens": tokens,
    } 


# REPLACE WITH ACTION METRICS LATER

def _build_abstained_metric(reason: str) -> Dict[str, Any]:
    """
    Build a metric object in the 'abstained' state as per your spec.
    This lets your frontend work against the final schema even before
    the real models are implemented.
    """
    return {
        "score_0_100": None,
        "label": "abstained",
        "confidence": 0.0,
        "abstained": True,
        "details": {
            "reason": reason,
        },
        "feedback": [],
    }


def _build_dummy_overall_score() -> Dict[str, Any]:
    """
    Temporary overall score. Replace this with your calibrated meta-model
    once you have individual metrics.
    """
    return {
        "score_0_100": 0,
        "label": "unknown",
        "confidence": 0.0,
    }


def _build_quality_flags(audio_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the quality_flags block.

    Now uses:
      - avg word probability -> asr_confidence
      - noise_summary.mic_quality -> mic_quality
      - noise_summary.noise_dbfs -> background_noise_level
      - noise_summary.speech_ratio + asr_confidence -> abstain_reason (if very low)
    """
   
    words = audio_json.get("words", []) or []
    probs = [
        w.get("probability")
        for w in words
        if isinstance(w, dict) and w.get("probability") is not None
    ]
    if probs:
        asr_confidence = float(sum(probs) / len(probs))
    else:
        asr_confidence = 0.0

    noise_summary = audio_json.get("noise_summary", {}) or {}
    mic_quality = noise_summary.get("mic_quality", "unknown")
    noise_dbfs = noise_summary.get("noise_dbfs")
    speech_ratio = float(noise_summary.get("speech_ratio", 0.0))

    # Simple mapping from noise_dbfs to qualitative noise level
    if noise_dbfs is None:
        background_noise_level = "unknown"
    elif noise_dbfs < -60:
        background_noise_level = "low"
    elif noise_dbfs < -40:
        background_noise_level = "medium"
    else:
        background_noise_level = "high"

    # Simple rule to decide abstain_reason (can refine later)
    abstain_reason: Optional[str] = None
    if asr_confidence < 0.5:
        abstain_reason = "low_asr_confidence"
    if speech_ratio < 0.3:
        # If both are bad, prefer a combined reason
        abstain_reason = (
            "low_speech_ratio"
            if abstain_reason is None
            else "low_asr_and_speech_ratio"
        )

    return {
        "asr_confidence": asr_confidence,
        "mic_quality": mic_quality,
        "background_noise_level": background_noise_level,
        "abstain_reason": abstain_reason,
    }


# ---- Main pipeline entrypoint ----------------------------------------------


def run_full_analysis(
    job_id: str,
    audio_path: Path,
    raw_input_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    High-level pipeline used by your job worker.

    This function is what your background worker / FastAPI layer will call:

        result = run_full_analysis(
            job_id=job_id,
            audio_path=local_audio_path,
            raw_input_payload=request_body_dict,
        )

    It:
      1. Calls audio_to_json(...) to get low-level audio + word features.
      2. Builds transcript, quality flags, and stub metric objects.
      3. Returns a dict that matches the JSON shape for:
         GET /api/v1/presentations/{job_id}/full

    Raises:
        ValueError: If input payload is invalid or audio file doesn't exist
        RuntimeError: If audio processing or metric computation fails
    """
    logger.info(f"Starting analysis for job_id={job_id}, audio_path={audio_path}")

    try:
        # Validate inputs
        if not isinstance(audio_path, Path):
            audio_path = Path(audio_path)

        if not audio_path.exists():
            error_msg = f"Audio file not found: {audio_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        if not audio_path.is_file():
            error_msg = f"Audio path is not a file: {audio_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate payload
        if not isinstance(raw_input_payload, dict):
            error_msg = "Input payload must be a dictionary"
            logger.error(error_msg)
            raise ValueError(error_msg)

        job_input = PresentationJobInput.from_dict(raw_input_payload)
        logger.debug(f"Parsed job input: {job_input}")

    except KeyError as e:
        error_msg = f"Missing required field in input payload: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        error_msg = f"Error validating inputs: {e}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e

    # 1) low-level analysis (Whisper, librosa, etc.)
    try:
        logger.info("Running audio_to_json processing")
        audio_json = audio_to_json(audio_path)
        logger.info("Audio processing completed successfully")
    except Exception as e:
        error_msg = f"Audio processing failed: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

    # audio_json is expected to look like:
    # {
    #   "audio_metadata": {...},
    #   "audio_features": {...},
    #   "words": [...],
    #   "pauses": [...],
    #   "vad_segments": [...],
    #   "silence_segments": [...],
    #   "vad_pause_segments": [...],
    #   "noise_summary": {...},
    # }

    # 2) Extract metadata and validate audio processing results
    try:
        audio_metadata = audio_json.get("audio_metadata", {})
        if not audio_metadata:
            logger.warning("Audio metadata is empty")

        words = audio_json.get("words", []) or []
        if not words:
            logger.warning("No words found in transcription - audio may be silent or ASR failed")

        duration_sec = float(audio_metadata.get("duration", audio_metadata.get("duration_sec", 0.0)))
        if duration_sec <= 0:
            logger.warning(f"Invalid or zero duration: {duration_sec}")

        logger.debug(f"Audio duration: {duration_sec}s, word count: {len(words)}")

    except (TypeError, ValueError) as e:
        error_msg = f"Error extracting audio metadata: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # 3) transcript block (used by both /full and /transcript endpoints)
    try:
        logger.debug("Building transcript from words")
        transcript_block = _build_transcript_from_words(words)
    except Exception as e:
        error_msg = f"Error building transcript: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

    # 4) quality flags & overall score
    try:
        logger.debug("Computing quality flags")
        quality_flags = _build_quality_flags(audio_json)
        overall_score = _build_dummy_overall_score()
    except Exception as e:
        error_msg = f"Error computing quality flags: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e

    # 5) metrics
    requested = job_input.requested_metrics or [
        "pace",
        "pause_quality",
        "fillers",
        "intonation",
        "articulation",
        "content_structure",
        "confidence_cv",
    ]

    logger.info(f"Computing metrics: {requested}")
    metrics: Dict[str, Any] = {}
    timeline: List[Dict[str, Any]] = []  # Initialize timeline here to collect from metrics

    for metric_name in requested:
        try:
            if metric_name == "pace":
                logger.debug("Computing pace metric")
                metrics["pace"] = compute_pace_metric(words, duration_sec)

            elif metric_name == "pause_quality":
                logger.debug("Computing pause_quality metric")
                pause_metric, pause_timeline = compute_pause_quality_metric(
                    audio_json.get("word_pauses", []),
                    audio_json.get("vad_silence_segments", []),
                    duration_sec
                )
                metrics["pause_quality"] = pause_metric
                # Add pause timeline events to the main timeline
                timeline.extend(pause_timeline)

            elif metric_name == "fillers":
                logger.debug("Computing fillers metric")
                metrics["fillers"] = compute_fillers_metric(words, duration_sec)

            elif metric_name == "intonation":
                logger.debug("Computing intonation metric")
                audio_features = audio_json.get("audio_features", {})
                raw_pitch_hz = audio_json.get("raw_pitch_hz")  # NEW: pass raw pitch for exact range
                metrics["intonation"] = compute_intonation_metric(
                    audio_features, duration_sec, raw_pitch_hz=raw_pitch_hz
                )

            else:
                logger.debug(f"Metric '{metric_name}' not implemented, abstaining")
                metrics[metric_name] = _build_abstained_metric(
                    reason="metric_not_implemented_yet"
                )

        except Exception as e:
            error_msg = f"Error computing metric '{metric_name}': {e}"
            logger.error(error_msg, exc_info=True)
            # Instead of failing the entire job, abstain this metric
            metrics[metric_name] = _build_abstained_metric(
                reason=f"metric_computation_failed: {str(e)}"
            )

    # 6) model metadata: stubbed for now; fill with real versions later
    model_metadata = {
        "asr_model": "whisper-small",
        "vad_model": "silero-vad",
        "embedding_model": "not_configured",
        "version": "dev-0.0.2",
    }

    # 7) Build the final response dict that matches your
    #    GET /api/v1/presentations/{job_id}/full spec.
    try:
        input_block = job_input.to_dict()
        input_block["duration_sec"] = duration_sec

        full_response: Dict[str, Any] = {
            "job_id": job_id,
            "status": "done",
            "input": input_block,
            "quality_flags": quality_flags,
            "overall_score": overall_score,
            "metrics": metrics,
            "timeline": timeline,
            "model_metadata": model_metadata,
            "transcript": {
                "full_text": transcript_block["full_text"],
                "language": transcript_block["language"],
            },
        }

        logger.info(f"Analysis completed successfully for job_id={job_id}")
        return full_response

    except Exception as e:
        error_msg = f"Error building final response: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e


# ---- Convenience function for /transcript endpoint -------------------------


def build_transcript_response(
    job_id: str,
    status: str,
    transcript_block: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Helper to build the JSON for:
      GET /api/v1/presentations/{job_id}/transcript

    - If status != "done", you can return { "job_id": ..., "status": "processing" } etc.
    - If status == "done", transcript_block should be the object from
      _build_transcript_from_words(...) and we embed it.
    """
    if status != "done" or not transcript_block:
        return {
            "job_id": job_id,
            "status": status,
        }

    return {
        "job_id": job_id,
        "status": "done",
        "transcript": deepcopy(transcript_block),
    }
