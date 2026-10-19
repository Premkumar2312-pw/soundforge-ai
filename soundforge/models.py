"""
Pydantic data models for SoundForge AI (PS1 Specification)
Full dual-compatibility with IncuBrix Assessment Contract and existing API.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    # Backward compatibility aliases
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"

class MusicalSection(BaseModel):
    mood: Optional[str] = Field(None, description="Mood or section type, e.g. 'intro', 'verse', 'chorus', 'outro'")
    start_s: Optional[float] = Field(None, ge=0.0, description="Start offset in seconds")
    name: Optional[str] = Field(None, description="Section name")
    duration: Optional[float] = Field(None, gt=0.0, description="Duration in seconds")
    start_time: Optional[float] = Field(None, description="Start time in seconds")
    end_time: Optional[float] = Field(None, description="End time in seconds")
    start_bar: Optional[int] = Field(None, description="Start bar index (0-indexed)")
    end_bar: Optional[int] = Field(None, description="End bar index (0-indexed)")

    @model_validator(mode="before")
    @classmethod
    def reconcile_section_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Sync mood and name
            mood = values.get("mood")
            name = values.get("name")
            if mood and not name:
                values["name"] = mood
            elif name and not mood:
                values["mood"] = name
            elif not mood and not name:
                values["name"] = "section"
                values["mood"] = "section"

            # Sync start_s and start_time
            start_s = values.get("start_s")
            start_time = values.get("start_time")
            if start_s is not None and start_time is None:
                values["start_time"] = float(start_s)
            elif start_time is not None and start_s is None:
                values["start_s"] = float(start_time)
        return values

class OutputSettings(BaseModel):
    sample_rate: int = Field(48000, description="Audio sample rate in Hz (44100, 48000, 96000)")
    target_lufs: float = Field(-16.0, ge=-36.0, le=-6.0, description="Target integrated loudness in LUFS")
    formats: List[str] = Field(default_factory=lambda: ["wav"], description="Output formats: ['wav', 'mp3']")

    @field_validator("sample_rate")
    def validate_sample_rate(cls, v: int) -> int:
        if v not in [44100, 48000, 96000]:
            raise ValueError("Sample rate must be 44100, 48000, or 96000 Hz")
        return v

    @field_validator("formats")
    def validate_formats(cls, v: List[str]) -> List[str]:
        valid = {"wav", "mp3"}
        lower_v = [f.lower() for f in v]
        for f in lower_v:
            if f not in valid:
                raise ValueError(f"Unsupported output format '{f}'. Supported: ['wav', 'mp3']")
        if "wav" not in lower_v:
            lower_v.insert(0, "wav")
        return lower_v

class MusicJobRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="Natural language description of desired music")
    duration_s: Optional[float] = Field(None, ge=5.0, le=300.0, description="Exact duration in seconds (5.0 to 300.0s)")
    duration: Optional[float] = Field(None, ge=5.0, le=300.0, description="Alias for duration_s")
    sections: Optional[List[MusicalSection]] = Field(None, description="Optional custom musical sections")
    tempo_bpm: Optional[float] = Field(None, ge=40.0, le=240.0, description="Tempo in beats per minute")
    tempo: Optional[float] = Field(None, ge=40.0, le=240.0, description="Alias for tempo_bpm")
    key: Optional[str] = Field(None, description="Musical key/tonality, e.g. 'C_major', 'A_minor'")
    loopable: Optional[bool] = Field(None, description="Whether track is engineered for seamless looping")
    loopability: Optional[bool] = Field(None, description="Alias for loopable")
    narration_url: Optional[str] = Field(None, description="URL or filepath to narration audio for sidechain ducking")
    seed: Optional[int] = Field(None, description="Random seed for reproducible generation")
    output: Optional[OutputSettings] = Field(None, description="Output settings (sample rate, target LUFS, formats)")
    sample_rate: Optional[int] = Field(48000, description="Top-level fallback for sample rate")
    target_loudness: Optional[float] = Field(-16.0, ge=-36.0, le=-6.0, description="Top-level fallback for target LUFS")
    output_formats: Optional[List[str]] = Field(default_factory=lambda: ["wav"], description="Top-level fallback for output formats")
    callback_url: Optional[str] = Field(None, description="Webhook URL notified upon job completion")

    @model_validator(mode="before")
    @classmethod
    def reconcile_request_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        # 1. Reconcile duration_s vs duration
        dur_s = values.get("duration_s")
        dur = values.get("duration")
        if dur_s is not None:
            chosen_dur = float(dur_s)
        elif dur is not None:
            chosen_dur = float(dur)
        else:
            raise ValueError("Field 'duration_s' (or 'duration') is required")

        if not (5.0 <= chosen_dur <= 300.0):
            raise ValueError(f"Duration must be between 5.0 and 300.0 seconds; received {chosen_dur}")
        values["duration_s"] = chosen_dur
        values["duration"] = chosen_dur

        # 2. Reconcile tempo_bpm vs tempo
        t_bpm = values.get("tempo_bpm")
        t = values.get("tempo")
        if t_bpm is not None:
            chosen_tempo = float(t_bpm)
        elif t is not None:
            chosen_tempo = float(t)
        else:
            chosen_tempo = None

        if chosen_tempo is not None:
            if not (40.0 <= chosen_tempo <= 240.0):
                raise ValueError(f"Tempo must be between 40.0 and 240.0 BPM; received {chosen_tempo}")
            values["tempo_bpm"] = chosen_tempo
            values["tempo"] = chosen_tempo

        # 3. Reconcile loopable vs loopability
        l_able = values.get("loopable")
        l_ability = values.get("loopability")
        if l_able is not None:
            chosen_loop = bool(l_able)
        elif l_ability is not None:
            chosen_loop = bool(l_ability)
        else:
            chosen_loop = False
        values["loopable"] = chosen_loop
        values["loopability"] = chosen_loop

        # 4. Reconcile nested output vs top-level output settings
        out = values.get("output")
        sr = values.get("sample_rate")
        tl = values.get("target_loudness")
        fmts = values.get("output_formats")

        if isinstance(out, dict):
            if "sample_rate" in out:
                sr = out["sample_rate"]
            if "target_lufs" in out:
                tl = out["target_lufs"]
            if "formats" in out:
                fmts = out["formats"]
        elif isinstance(out, OutputSettings):
            sr = out.sample_rate
            tl = out.target_lufs
            fmts = out.formats

        final_sr = int(sr) if sr is not None else 48000
        if final_sr not in [44100, 48000, 96000]:
            raise ValueError("Sample rate must be 44100, 48000, or 96000 Hz")

        final_tl = float(tl) if tl is not None else -16.0
        if not (-36.0 <= final_tl <= -6.0):
            raise ValueError("Target loudness must be between -36.0 and -6.0 LUFS")

        if fmts is not None:
            valid_fmts = {"wav", "mp3"}
            clean_fmts = [f.lower() for f in fmts]
            for f in clean_fmts:
                if f not in valid_fmts:
                    raise ValueError(f"Unsupported output format '{f}'. Supported: ['wav', 'mp3']")
            if "wav" not in clean_fmts:
                clean_fmts.insert(0, "wav")
            final_fmts = clean_fmts
        else:
            final_fmts = ["wav"]

        values["sample_rate"] = final_sr
        values["target_loudness"] = final_tl
        values["output_formats"] = final_fmts
        values["output"] = OutputSettings(
            sample_rate=final_sr,
            target_lufs=final_tl,
            formats=final_fmts
        )

        return values

class MusicJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    created_at: str
    estimated_duration_seconds: float
    idempotency_key: Optional[str] = None
    correlation_id: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Job progress from 0.0 to 1.0")
    progress_percent: Optional[int] = Field(0, ge=0, le=100, description="Job progress from 0 to 100")
    current_stage: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    artifacts: Optional[Dict[str, str]] = None
    manifest: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    storage: str
    ready: bool

class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)

class ErrorResponse(BaseModel):
    error: ErrorDetail
