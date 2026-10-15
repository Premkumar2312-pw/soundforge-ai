"""
Pydantic data models for SoundForge AI (PS1 Specification)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MusicalSection(BaseModel):
    name: str = Field(..., description="Section name, e.g. 'intro', 'verse', 'chorus', 'outro'")
    duration: float = Field(..., gt=0.0, description="Duration of this section in seconds")
    start_time: Optional[float] = Field(None, description="Start time in seconds")
    end_time: Optional[float] = Field(None, description="End time in seconds")
    start_bar: Optional[int] = Field(None, description="Start bar index (0-indexed)")
    end_bar: Optional[int] = Field(None, description="End bar index (0-indexed)")

class MusicJobRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="Natural language description of desired music")
    duration: float = Field(..., gt=0.0, le=600.0, description="Exact duration in seconds (1.0 to 600.0s)")
    sections: Optional[List[MusicalSection]] = Field(None, description="Optional custom musical sections")
    tempo: Optional[float] = Field(None, ge=40.0, le=240.0, description="Tempo in beats per minute (BPM)")
    key: Optional[str] = Field(None, description="Musical key/tonality, e.g. 'C_major', 'A_minor', 'G_major'")
    loopability: bool = Field(False, description="Whether the track is engineered for seamless looping")
    narration_url: Optional[str] = Field(None, description="URL or filepath to narration audio for automatic sidechain ducking")
    seed: Optional[int] = Field(None, description="Random seed for reproducible generation")
    sample_rate: int = Field(48000, description="Audio sample rate in Hz (default 48000)")
    target_loudness: float = Field(-14.0, ge=-36.0, le=-6.0, description="Target integrated loudness in LUFS (default -14.0 LUFS)")
    output_formats: List[str] = Field(default_factory=lambda: ["wav"], description="Requested audio formats: ['wav', 'mp3']")
    callback_url: Optional[str] = Field(None, description="Webhook URL notified upon job completion")

    @field_validator("sample_rate")
    def validate_sample_rate(cls, v: int) -> int:
        if v not in [44100, 48000, 96000]:
            raise ValueError("Sample rate must be 44100, 48000, or 96000 Hz")
        return v

    @field_validator("output_formats")
    def validate_output_formats(cls, v: List[str]) -> List[str]:
        valid_formats = {"wav", "mp3"}
        lower_v = [fmt.lower() for fmt in v]
        for fmt in lower_v:
            if fmt not in valid_formats:
                raise ValueError(f"Unsupported output format '{fmt}'. Supported: ['wav', 'mp3']")
        if "wav" not in lower_v:
            lower_v.insert(0, "wav")  # WAV is always guaranteed
        return lower_v

class MusicJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    created_at: str
    estimated_duration_seconds: float
    idempotency_key: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Job progress from 0.0 to 1.0")
    current_stage: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    artifacts: Optional[Dict[str, str]] = None
    manifest: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    storage: str
    ready: bool
