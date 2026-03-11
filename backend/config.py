"""
Configuration Management
========================
Centralized configuration for the ATS Resume Checker application.
All environment variables are loaded here and exposed as typed constants.

Usage:
    from config import settings
    print(settings.GEMINI_API_KEY)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env file ──────────────────────────────────────────────────────────
load_dotenv()

# ── Path Constants ──────────────────────────────────────────────────────────
# Root of the backend directory (where this file lives)
BASE_DIR = Path(__file__).resolve().parent

# Directory for uploaded resume files
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")

# Directory for generated resume files (LaTeX + PDF output)
GENERATED_DIR = BASE_DIR / os.getenv("GENERATED_DIR", "generated")

# Directory containing LaTeX Jinja2 templates
TEMPLATES_DIR = BASE_DIR / "templates" / "latex"


class Settings:
    """
    Application settings loaded from environment variables.
    
    Attributes:
        GEMINI_API_KEY: Google Gemini API key for AI-powered features.
        BACKEND_PORT:   Port for the FastAPI server (default: 8000).
        FRONTEND_URL:   Frontend dev server URL for CORS (default: http://localhost:5173).
    """

    def __init__(self):
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        self.BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
        self.FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    @property
    def is_gemini_configured(self) -> bool:
        """Check if the Gemini API key is set and not a placeholder."""
        return bool(self.GEMINI_API_KEY) and self.GEMINI_API_KEY != "your_gemini_api_key_here"


# ── Singleton instance ──────────────────────────────────────────────────────
settings = Settings()
