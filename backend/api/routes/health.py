"""
Health Check Route
==================
Simple health check endpoint to verify the API is running
and check the status of connected services.
"""

from fastapi import APIRouter

from config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Check the health of the API and its dependencies.

    Returns:
        JSON with service status and configuration info.
    """
    return {
        "status": "healthy",
        "service": "ATS Resume Checker & Generator",
        "version": "1.0.0",
        "gemini_configured": settings.is_gemini_configured,
    }
