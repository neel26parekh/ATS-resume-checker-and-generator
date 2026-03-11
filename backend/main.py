"""
ATS Resume Checker — FastAPI Application
=========================================
Main entry point for the backend server. Sets up the FastAPI app,
registers all API route modules, and configures middleware.

Run with:
    uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings, UPLOAD_DIR, GENERATED_DIR
from api.routes import health, resume, scoring, generation


# ── Lifecycle Events ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for the FastAPI application.
    
    On startup:
        - Creates the uploads/ directory for temporary resume files.
        - Creates the generated/ directory for LaTeX output.
    """
    # Startup: ensure required directories exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📂 Upload directory:    {UPLOAD_DIR}")
    print(f"📂 Generated directory: {GENERATED_DIR}")
    print(f"🤖 Gemini API configured: {settings.is_gemini_configured}")

    yield  # Application runs here

    # Shutdown: cleanup if needed (currently no-op)
    print("👋 Shutting down ATS Resume Checker...")


# ── FastAPI Application ─────────────────────────────────────────────────────

app = FastAPI(
    title="ATS Resume Checker & Generator",
    description=(
        "An intelligent platform that checks ATS compatibility, scores resumes "
        "against job descriptions, and generates optimized LaTeX resumes."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS Middleware ──────────────────────────────────────────────────────────
# Allow the frontend dev server to make requests to the backend.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register API Routers ────────────────────────────────────────────────────
# Each router is a separate module in api/routes/ for clean separation.

app.include_router(health.router,     prefix="/api", tags=["Health"])
app.include_router(resume.router,     prefix="/api", tags=["Resume"])
app.include_router(scoring.router,    prefix="/api", tags=["Scoring"])
app.include_router(generation.router, prefix="/api", tags=["Generation"])
