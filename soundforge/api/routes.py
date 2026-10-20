"""
FastAPI Route Handlers for SoundForge AI (PS1 Specification & IncuBrix Integration Standard)
"""

import os
import uuid
import time
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status, Response, Request, UploadFile, File
import soundfile as sf
from fastapi.responses import FileResponse, HTMLResponse

from soundforge.models import (
    MusicJobRequest,
    MusicJobResponse,
    JobStatusResponse,
    JobStatus,
    HealthResponse
)
from soundforge.api.queue import job_manager
from soundforge.api.idempotency import idempotency_manager
from soundforge.storage import get_storage_provider
from soundforge.config import settings
from soundforge.utils.logging import logger

router = APIRouter()
storage = get_storage_provider()
SERVER_START_TIME = time.time()

@router.post(
    "/api/v1/music/jobs",
    response_model=MusicJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create background music generation job",
    description="Submits an asynchronous music generation job according to Problem Statement PS1 specification."
)
async def create_music_job(
    request: MusicJobRequest,
    response: Response,
    http_request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    corr_id = getattr(http_request.state, "correlation_id", str(uuid.uuid4()))
    active_idem_key = idempotency_key or request.idempotency_key

    # Idempotency check
    if active_idem_key:
        payload_hash = idempotency_manager.compute_payload_hash(request.model_dump())
        cached = idempotency_manager.get(active_idem_key)
        if cached:
            if cached.payload_hash == payload_hash:
                logger.info(f"Idempotent request recognized for key {active_idem_key}", extra={"correlation_id": corr_id})
                response.status_code = status.HTTP_202_ACCEPTED
                cached_resp = cached.response_payload.copy()
                cached_resp["correlation_id"] = corr_id
                return MusicJobResponse(**cached_resp)
            else:
                logger.warning(f"Idempotency conflict for key {active_idem_key}", extra={"correlation_id": corr_id})
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key collision with differing request payload."
                )

    job_id = str(uuid.uuid4())
    job_state = job_manager.create_job(job_id, request, correlation_id=corr_id)

    # Launch background task
    import asyncio
    asyncio.create_task(job_manager.run_job(job_id))

    est_duration = max(1.5, round(request.duration * 0.12, 1))

    resp_payload = {
        "job_id": job_id,
        "status": JobStatus.QUEUED,
        "message": "Background music generation job accepted and enqueued.",
        "created_at": job_state.created_at,
        "estimated_duration_seconds": est_duration,
        "idempotency_key": active_idem_key,
        "correlation_id": corr_id
    }

    if active_idem_key:
        idempotency_manager.register(active_idem_key, payload_hash, resp_payload)

    return MusicJobResponse(**resp_payload)

@router.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status (Assessment Contract)",
    description="Poll progress, execution status, manifest, and download URLs for a job."
)
@router.get(
    "/api/v1/music/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get music generation job status (Alias)",
    description="Poll progress, execution status, manifest, and download URLs for a job."
)
async def get_job_status(job_id: str, http_request: Request):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found."
        )

    corr_id = job.correlation_id or getattr(http_request.state, "correlation_id", None)
    is_done = job.status in (JobStatus.SUCCEEDED, JobStatus.COMPLETED)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=round(job.progress, 2),
        progress_percent=int(job.progress * 100),
        current_stage=job.current_stage,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error=job.error,
        artifacts=job.artifacts if is_done else None,
        manifest=job.manifest if is_done else None,
        correlation_id=corr_id
    )

@router.get(
    "/api/v1/jobs/{job_id}/artifacts/{filename:path}",
    summary="Download generation artifact (Assessment Contract)",
    description="Download master mix, MP3, separate stems, or JSON manifest."
)
@router.get(
    "/api/v1/music/jobs/{job_id}/artifacts/{filename:path}",
    summary="Download generation artifact (Alias)",
    description="Download master mix, MP3, separate stems, or JSON manifest."
)
async def download_artifact(job_id: str, filename: str):
    job = job_manager.get_job(job_id)
    if not job:
        # Check if files exist directly in storage
        if not storage.artifact_exists(job_id, filename):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job or artifact '{filename}' not found.")
    else:
        if job.status not in (JobStatus.SUCCEEDED, JobStatus.COMPLETED):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is {job.status.value}")

    file_path = storage.get_artifact_path(job_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact '{filename}' not found.")

    media_types = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".json": "application/json"
    }
    ext = os.path.splitext(filename)[1].lower()
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=os.path.basename(filename)
    )

@router.post(
    "/api/v1/narration/upload",
    summary="Upload narration audio for sidechain ducking",
    description="Accepts WAV or MP3 audio up to 50 MB and returns a local narration URL for use in generation requests."
)
@router.post(
    "/api/v1/audio/upload",
    summary="Upload audio file (Alias)",
    description="Upload audio file for processing or narration."
)
async def upload_narration_audio(file: UploadFile = File(...)):
    filename = file.filename or "narration.wav"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".wav", ".mp3"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .wav and .mp3 narration files are supported."
        )

    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file exceeds 50 MB limit."
        )
    if len(contents) < 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio file is empty or corrupted."
        )

    upload_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.STORAGE_DIR, "_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{upload_id}_{os.path.basename(filename)}"
    file_path = os.path.join(upload_dir, safe_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        data, sr = sf.read(file_path)
        dur = round(len(data) / sr, 2)
    except Exception as ex:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid or corrupted audio file: {ex}"
        )

    narration_url = f"/api/v1/narration/files/{safe_name}"
    return {
        "status": "uploaded",
        "narration_url": narration_url,
        "filename": filename,
        "duration_s": dur,
        "sample_rate": sr,
        "file_size_bytes": len(contents)
    }

@router.get(
    "/api/v1/narration/files/{filename}",
    summary="Download or stream uploaded narration audio",
    description="Retrieves previously uploaded narration audio."
)
async def get_uploaded_narration(filename: str):
    safe_basename = os.path.basename(filename)
    upload_dir = os.path.join(settings.STORAGE_DIR, "_uploads")
    file_path = os.path.join(upload_dir, safe_basename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Narration file not found.")
    ext = os.path.splitext(safe_basename)[1].lower()
    media_type = "audio/wav" if ext == ".wav" else "audio/mpeg"
    return FileResponse(file_path, media_type=media_type, filename=safe_basename)

@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
@router.get("/api/v1/health", response_model=HealthResponse, summary="API v1 Liveness probe")
async def health_check():
    uptime = time.time() - SERVER_START_TIME
    return HealthResponse(
        status="ok",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        storage=settings.STORAGE_BACKEND,
        ready=True
    )

@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
@router.get("/api/v1/ready", response_model=HealthResponse, summary="API v1 Readiness probe")
async def readiness_check():
    uptime = time.time() - SERVER_START_TIME
    try:
        test_dir = storage.get_job_dir(".readiness-probe")
        is_ready = os.path.exists(test_dir)
    except Exception:
        is_ready = False

    if not is_ready:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Storage not ready")

    return HealthResponse(
        status="ready",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        storage=settings.STORAGE_BACKEND,
        ready=True
    )
