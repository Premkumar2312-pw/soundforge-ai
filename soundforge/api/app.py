"""
FastAPI Application Entrypoint for SoundForge AI
PS1 Specification & IncuBrix Integration Standard Compliant
"""

import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from soundforge import __version__
from soundforge.api.routes import router
from soundforge.api.ui import DEMO_HTML
from soundforge.config import settings
from soundforge.utils.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SoundForge AI service started", extra={"version": __version__, "env": settings.APP_ENV})
    yield
    logger.info("SoundForge AI service shutting down")

app = FastAPI(
    title="SoundForge AI - Background Music Engine for Video",
    description=r"""
# SoundForge AI REST API (IncuBrix PS1 Specification)

Professional AI Background Music Engine for Video, conforming to IncuBrix Problem Statement PS1 specifications.

### Key Capabilities:
- **Asynchronous Background Processing**: HTTP 202 Accepted, job IDs, real-time progress polling.
- **Genuine Multi-Track Instrument Stems**: Zero frequency-splitting policy; procedural independent synthesis of Drums, Bass, Chords, and Melody.
- **Mathematical Reconstruction Guarantee**: Master mix mathematically reconstructs from stems using documented linear weights ($Mix = \sum g_i \cdot Stem_i$).
- **Loudness & Peak Mastering**: ITU-R BS.1770-4 / EBU R128 loudness normalization and True Peak brickwall limiting ($\le -1.0$ dBTP).
- **Sidechain Narration Ducking**: Automatic voice envelope detection and smooth ducking attenuation.
- **PS1 Manifest**: Full provenance, beat/bar grid, section timings, licensing, and audio metrics.
- **Idempotency**: Transparent deduplication via `Idempotency-Key` headers.
- **100% Cleared Commercial Licensing**: Zero proprietary soundfonts, samples, or restrictive weights.
    """,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Correlation ID Middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.correlation_id = corr_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = corr_id
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Structured Error Handlers (Integration Standard #5)
# Shape: {"error":{"code":"UPPER_SNAKE_CASE","message":"...","retryable":false,"details":{}}}
# -------------------------------------------------------------

STATUS_CODE_TO_ERROR_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "IDEMPOTENCY_CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_SERVER_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT"
}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic schema validation errors to IncuBrix structured error schema."""
    details = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        details.append({"location": loc, "issue": msg})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload validation failed.",
                "retryable": False,
                "details": {"validation_errors": details}
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Format standard HTTP exceptions to IncuBrix structured error schema."""
    err_code = STATUS_CODE_TO_ERROR_CODE.get(exc.status_code, "HTTP_ERROR")
    if exc.status_code == 409:
        err_code = "IDEMPOTENCY_CONFLICT"
    elif exc.status_code == 404:
        err_code = "NOT_FOUND"

    retryable = exc.status_code in (502, 503, 504, 429)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": err_code,
                "message": str(exc.detail),
                "retryable": retryable,
                "details": {}
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions to prevent stack trace leakage."""
    corr_id = getattr(request.state, "correlation_id", "unknown")
    logger.exception(f"Unhandled exception: {exc}", extra={"correlation_id": corr_id})

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "retryable": True,
                "details": {"correlation_id": corr_id}
            }
        }
    )

# Include API routes
app.include_router(router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
async def serve_demonstration_ui():
    """Serves the interactive web demonstration interface."""
    return HTMLResponse(content=DEMO_HTML)
