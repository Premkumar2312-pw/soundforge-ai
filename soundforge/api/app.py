"""
FastAPI Application Entrypoint for SoundForge AI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from soundforge import __version__
from soundforge.api.routes import router
from soundforge.api.ui import DEMO_HTML
from soundforge.config import settings
from soundforge.utils.logging import logger

app = FastAPI(
    title="SoundForge AI - Background Music Engine for Video",
    description="""
# SoundForge AI REST API (PS1 Specification)

Professional AI Background Music Engine for Video, conforming to Problem Statement PS1 specifications.

### Key Capabilities:
- **Asynchronous Background Processing**: HTTP 202 Accepted, job IDs, real-time progress polling.
- **Genuine Multi-Track Instrument Stems**: Zero frequency-splitting policy; procedural independent synthesis of Drums, Bass, Chords, and Melody.
- **Mathematical Reconstruction Guarantee**: Master mix mathematically reconstructs from stems using documented linear weights ($Mix = \\sum g_i \\cdot Stem_i$).
- **Loudness & Peak Mastering**: ITU-R BS.1770-4 / EBU R128 loudness normalization and True Peak brickwall limiting ($\le -1.0$ dBTP).
- **Sidechain Narration Ducking**: Automatic voice envelope detection and smooth ducking attenuation.
- **PS1 Manifest**: Full provenance, beat/bar grid, section timings, licensing, and audio metrics.
- **Idempotency**: Transparent deduplication via `Idempotency-Key` headers.
- **100% Cleared Commercial Licensing**: Zero proprietary soundfonts, samples, or restrictive weights.
    """,
    version=__version__,
    openapi_version="3.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
async def serve_demonstration_ui():
    """Serves the interactive web demonstration interface."""
    return HTMLResponse(content=DEMO_HTML)

@app.on_event("startup")
async def on_startup():
    logger.info("SoundForge AI service started", extra={"version": __version__, "env": settings.APP_ENV})

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("SoundForge AI service shutting down")
