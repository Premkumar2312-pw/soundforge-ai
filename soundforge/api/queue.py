"""
Background Job Manager and Task Queue for SoundForge AI
Handles asynchronous music generation, stage updates, progress, and callbacks.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx

from soundforge.models import JobStatus, MusicJobRequest, JobStatusResponse
from soundforge.engine.generator import execute_generation_pipeline
from soundforge.storage import get_storage_provider
from soundforge.utils.logging import logger

class JobState:
    def __init__(self, job_id: str, request: MusicJobRequest):
        self.job_id = job_id
        self.request = request
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.current_stage = "Job received"
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

    def create_job(self, job_id: str, request: MusicJobRequest) -> JobState:
        state = JobState(job_id, request)
        self._jobs[job_id] = state
        return state

    def get_job(self, job_id: str) -> Optional[JobState]:
        return self._jobs.get(job_id)

    async def run_job(self, job_id: str):
        job = self.get_job(job_id)
        if not job:
            return

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc).isoformat()
        job_dir = self.storage.get_job_dir(job_id)

        def progress_tracker(progress: float, stage: str):
            job.progress = progress
            job.current_stage = stage

        try:
            manifest = await execute_generation_pipeline(
                job_id=job_id,
                request=job.request,
                output_dir=job_dir,
                progress_callback=progress_tracker
            )
            job.manifest = manifest
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
            job.current_stage = "Completed"
            job.completed_at = datetime.now(timezone.utc).isoformat()

            # Populate artifact endpoints
            base_artifact_route = f"/api/v1/music/jobs/{job_id}/artifacts"
            artifacts = {
                "mix_wav": f"{base_artifact_route}/mix.wav",
                "stem_drums": f"{base_artifact_route}/stem_drums.wav",
                "stem_bass": f"{base_artifact_route}/stem_bass.wav",
                "stem_chords": f"{base_artifact_route}/stem_chords.wav",
                "stem_melody": f"{base_artifact_route}/stem_melody.wav",
                "manifest_json": f"{base_artifact_route}/manifest.json"
            }
            if "mp3" in [fmt.lower() for fmt in job.request.output_formats]:
                artifacts["mix_mp3"] = f"{base_artifact_route}/mix.mp3"
            if manifest.get("ducking", {}).get("ducking_applied"):
                artifacts["ducked_mix_wav"] = f"{base_artifact_route}/ducked_mix.wav"

            job.artifacts = artifacts
            logger.info(f"Job {job_id} successfully completed", extra={"job_id": job_id})

            # Fire webhook callback if specified
            if job.request.callback_url:
                await self._fire_callback(job.request.callback_url, job)

        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}", extra={"job_id": job_id})
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.current_stage = f"Failed: {str(e)}"
            job.completed_at = datetime.now(timezone.utc).isoformat()

            if job.request.callback_url:
                await self._fire_callback(job.request.callback_url, job)

    async def _fire_callback(self, url: str, job: JobState):
        try:
            payload = {
                "job_id": job.job_id,
                "status": job.status.value,
                "completed_at": job.completed_at,
                "error": job.error,
                "artifacts": job.artifacts
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json=payload)
                logger.info(f"Callback sent to {url} for job {job.job_id}")
        except Exception as ex:
            logger.warning(f"Callback failed for job {job.job_id}: {ex}")

job_manager = JobManager()
