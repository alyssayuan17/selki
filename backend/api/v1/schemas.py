"""
Pydantic schemas for API request/response validation.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas
# ============================================================================

class PresentationCreateRequest(BaseModel):
    """POST /api/v1/presentations request body"""
    audio_url: str
    video_url: Optional[str] = None
    language: str = "en"
    talk_type: str
    audience_type: str
    requested_metrics: List[str] = Field(default_factory=lambda: [
        "pace",
        "pause_quality",
        "fillers",
        "intonation",
        "content_structure",
        "confidence_cv",
    ])
    user_metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Response Schemas - Common
# ============================================================================

class InputBlock(BaseModel):
    """Input data block (appears in multiple responses)"""
    audio_url: str
    video_url: Optional[str] = None
    language: str
    talk_type: str
    audience_type: str
    requested_metrics: List[str]
    user_metadata: Dict[str, Any]
    duration_sec: Optional[float] = None


class QualityFlags(BaseModel):
    """Quality assessment of audio/ASR"""
    asr_confidence: float
    mic_quality: str
    background_noise_level: str
    abstain_reason: Optional[str] = None


class OverallScore(BaseModel):
    """Overall presentation score"""
    score_0_100: int
    label: str
    confidence: float


class FailureInfo(BaseModel):
    """Failure details"""
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Response Schemas - POST /api/v1/presentations
# ============================================================================

class PresentationCreateResponse(BaseModel):
    """201 Created response"""
    job_id: str
    status: str  # "queued"
    created_at: datetime
    input: InputBlock


# ============================================================================
# Response Schemas - GET /api/v1/presentations/{job_id}
# ============================================================================

class PresentationStatusProcessing(BaseModel):
    """Status response while processing"""
    job_id: str
    status: str  # "processing"
    created_at: datetime
    updated_at: datetime


class PresentationStatusDone(BaseModel):
    """Status response when done"""
    job_id: str
    status: str  # "done"
    created_at: datetime
    updated_at: datetime
    input: InputBlock
    quality_flags: QualityFlags
    overall_score: OverallScore
    available_metrics: List[str]


class PresentationStatusFailed(BaseModel):
    """Status response when failed"""
    job_id: str
    status: str  # "failed"
    created_at: datetime
    updated_at: datetime
    failure: FailureInfo


# ============================================================================
# Response Schemas - GET /api/v1/presentations/{job_id}/full
# ============================================================================

class MetricFeedback(BaseModel):
    """Single feedback item"""
    start_sec: float
    end_sec: float
    message: str
    tip_type: str


class MetricResult(BaseModel):
    """Individual metric result"""
    score_0_100: Optional[int] = None
    label: str
    confidence: float
    abstained: bool = False
    details: Dict[str, Any]
    feedback: List[MetricFeedback] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    """Timeline segment"""
    start_sec: float
    end_sec: float
    dominant_issues: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)


class ModelMetadata(BaseModel):
    """Model version info"""
    asr_model: str
    vad_model: str
    embedding_model: str
    version: str


class TranscriptBlock(BaseModel):
    """Transcript info"""
    full_text: str
    language: str


class PresentationFullResponse(BaseModel):
    """Full detailed response"""
    job_id: str
    status: str  # "done"
    input: InputBlock
    quality_flags: QualityFlags
    overall_score: OverallScore
    metrics: Dict[str, MetricResult]
    timeline: List[TimelineEvent]
    model_metadata: ModelMetadata
    transcript: TranscriptBlock


# ============================================================================
# Response Schemas - GET /api/v1/presentations/{job_id}/transcript
# ============================================================================

class TranscriptSegment(BaseModel):
    """Transcript segment"""
    start_sec: float
    end_sec: float
    text: str
    avg_confidence: float


class TranscriptToken(BaseModel):
    """Individual token"""
    text: str
    start_sec: float
    end_sec: float
    is_filler: bool


class TranscriptDetailed(BaseModel):
    """Detailed transcript with segments and tokens"""
    full_text: str
    language: str
    segments: List[TranscriptSegment] = Field(default_factory=list)
    tokens: List[TranscriptToken] = Field(default_factory=list)


class PresentationTranscriptResponse(BaseModel):
    """Transcript response when done"""
    job_id: str
    status: str  # "done"
    transcript: TranscriptDetailed


class PresentationTranscriptProcessing(BaseModel):
    """Transcript response while processing"""
    job_id: str
    status: str  # "processing"
