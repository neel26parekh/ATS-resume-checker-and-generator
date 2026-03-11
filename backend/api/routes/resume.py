"""
Resume Routes
=============
Endpoints for uploading and parsing resume files (PDF/DOCX).

Endpoints:
    POST /api/resume/parse  — Upload a resume file and get parsed data.
"""

from fastapi import APIRouter, File, UploadFile, HTTPException

from api.models.resume import ResumeUploadResponse
from services.resume_parser import parse_resume
from utils.file_handling import save_upload

router = APIRouter()


@router.post("/resume/parse", response_model=ResumeUploadResponse)
async def parse_resume_endpoint(file: UploadFile = File(...)):
    """
    Upload and parse a resume file.

    Accepts PDF and DOCX files. Extracts text, detects sections,
    identifies contact information, and checks for formatting issues.

    Args:
        file: The uploaded resume file (multipart form data).

    Returns:
        ResumeUploadResponse with parsed resume data.

    Raises:
        400: If the file type is not supported.
        500: If parsing fails due to an internal error.
    """
    # Validate file is provided
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    try:
        # Save the uploaded file to disk
        saved_path = await save_upload(file)

        # Parse the resume
        resume_data = parse_resume(saved_path)

        # Clean up the uploaded file (we've already parsed it)
        saved_path.unlink(missing_ok=True)

        return ResumeUploadResponse(
            success=True,
            message=f"Successfully parsed {file.filename}",
            resume_data=resume_data,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse resume: {str(e)}",
        )
