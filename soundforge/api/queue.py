"""
Background Job Manager and Task Queue for SoundForge AI
Handles asynchronous music generation, stage updates, progress, and HMAC-signed callbacks.
"""

import asyncio
import hmac
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx

from soundforge.models import JobStatus, MusicJobRequest, JobStatusResponse
from soundforge.providers import get_provider
from soundforge.storage import get_storage_provider
from soundforge.config import settings
from soundforge.utils.logging import logger

class JobState:
    def __init__(self, job_id: str, request: MusicJobRequest, correlation_id: Optional[str] = None):
        self.job_id = job_id
        self.request = request
        self.correlation_id = correlation_id
        self.status = JobStatus.QUEUED
        self.progress = 0.0
        self.current_stage = "Job queued"
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.error: Optional[str] = None
        self.manifest: Optional[Dict[str, Any]] = None
        self.artifacts: Dict[str, str] = {}

class JobManager:
    def __init__(self):
        self._jobs: Dict[str, JobState] = {}
        self._lock = asyncio.Lock()
        self.storage = get_storage_provider()

    def create_job(self, job_id: str, request: MusicJobRequest, correlation_id: Optional[str] = None) -> JobState:
        state = JobState(job_id, request, correlation_id)
        self._jobs[job_id] = state
        return state

    def get_job(self, job_id: str) -> Optional[JobState]:
        return self._jobs.get(job_id)

    async def run_job(self, job_id: str):
        job = self.get_job(job_id)
        if not job:
            return

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc).isoformat()
        job_dir = self.storage.get_job_dir(job_id)

        def progress_tracker(progress: float, stage: str):
            job.progress = progress
            job.current_stage = stage

        try:
            provider = get_provider()
            manifest = await provider.generate(
                job_id=job_id,
                request=job.request,
                output_dir=job_dir,
                progress_callback=progress_tracker
            )
            job.manifest = manifest
            job.status = JobStatus.SUCCEEDED
            job.progress = 1.0
            job.current_stage = "Succeeded"
            job.completed_at = datetime.now(timezone.utc).isoformat()

            # Populate artifact endpoints (dual paths under /api/v1/jobs/ and /api/v1/music/jobs/)
            base_art = f"/api/v1/jobs/{job_id}/artifacts"
            artifacts = {
                "mix_wav": f"{base_art}/mix.wav",
                "stem_drums": f"{base_art}/stem_drums.wav",
                "stem_bass": f"{base_art}/stem_bass.wav",
                "stem_chords": f"{base_art}/stem_chords.wav",
                "stem_melody": f"{base_art}/stem_melody.wav",
                "music_manifest_json": f"{base_art}/music_manifest.json",
                "manifest_json": f"{base_art}/manifest.json"
            }
            if "mp3" in [fmt.lower() for fmt in job.request.output_formats]:
                if os.path.exists(os.path.join(job_dir, "mix.mp3")):
                    artifacts["mix_mp3"] = f"{base_art}/mix.mp3"
            if manifest.get("ducking", {}).get("ducking_applied"):
                artifacts["mix_ducked_wav"] = f"{base_art}/mix_ducked.wav"
                artifacts["ducked_mix_wav"] = f"{base_art}/ducked_mix.wav"

            job.artifacts = artifacts
            logger.info(f"Job {job_id} successfully completed", extra={"job_id": job_id, "correlation_id": job.correlation_id})

            # Fire HMAC-SHA256 signed webhook callback if specified
            if job.request.callback_url:
                await self._fire_callback(job.request.callback_url, job)

        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}", extra={"job_id": job_id, "correlation_id": job.correlation_id})
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.current_stage = f"Failed: {str(e)}"
            job.completed_at = datetime.now(timezone.utc).isoformat()

            if job.request.callback_url:
                await self._fire_callback(job.request.callback_url, job)

    async def _fire_callback(self, url: str, job: JobState):
        """Fire HTTP webhook callback with HMAC-SHA256 signature in X-IncuBrix-Signature header."""
        try:
            payload = {
                "job_id": job.job_id,
                "status": job.status.value,
                "completed_at": job.completed_at,
                "error": job.error,
                "artifacts": job.artifacts,
                "correlation_id": job.correlation_id
            }
            payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
            secret = settings.CALLBACK_SIGNING_SECRET.encode("utf-8")
            signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "X-IncuBrix-Signature": signature,
                "X-Correlation-ID": job.correlation_id or ""
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, content=payload_bytes, headers=headers)
                logger.info(f"Callback delivered to {url} (HTTP {resp.status_code}) for job {job.job_id}")
        except Exception as ex:
            logger.warning(f"Callback failed for job {job.job_id}: {ex}")

job_manager = JobManager()
