"""
Resume Generation Routes
========================
Endpoints for AI-powered resume generation with LaTeX output.

Endpoints:
    POST /api/generate          — Generate a tailored resume (PDF + .tex).
    GET  /api/templates         — List available LaTeX templates.
    GET  /api/download/{job_id} — Download generated files.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import GENERATED_DIR
from services.resume_generator import generate_resume
from services.jd_analyzer import analyze_job_description
from services.latex_compiler import render_and_compile, get_available_templates

router = APIRouter()


# ── Request Model ───────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    """Request body for the resume generation endpoint."""

    profile: dict = Field(
        ...,
        description="User profile data (name, experience, skills, education, etc.)",
    )
    job_description_text: str = Field(
        ...,
        description="Raw job description text",
    )
    template_id: str = Field(
        default="jake_resume",
        description="LaTeX template ID to use",
    )


class GenerateResponse(BaseModel):
    """Response from the resume generation endpoint."""

    success: bool
    message: str
    job_id: str | None = None
    pdf_available: bool = False
    tex_available: bool = True
    download_url_pdf: str | None = None
    download_url_tex: str | None = None
    compilation_error: str | None = None


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/templates")
async def list_templates():
    """
    List all available LaTeX resume templates.

    Returns:
        List of template objects with id, name, and description.
    """
    return {
        "templates": get_available_templates(),
    }


@router.post("/generate", response_model=GenerateResponse)
async def generate_resume_endpoint(request: GenerateRequest):
    """
    Generate an ATS-optimized resume tailored to a job description.

    Pipeline:
    1. Analyze the job description to extract keywords
    2. Generate resume content using AI (tailored to JD)
    3. Render LaTeX template with the generated content
    4. Compile to PDF

    Args:
        request: GenerateRequest with profile data, JD text, and template ID.

    Returns:
        GenerateResponse with download URLs for PDF and .tex files.

    Raises:
        400: If profile data is missing.
        503: If Gemini API is not configured.
        500: If generation or compilation fails.
    """
    if not request.profile:
        raise HTTPException(status_code=400, detail="Profile data is required.")
    if not request.job_description_text.strip():
        raise HTTPException(status_code=400, detail="Job description text is required.")

    try:
        # Step 1: Analyze the JD to extract keywords
        jd_data = await analyze_job_description(request.job_description_text)

        # Step 2: Generate resume content using AI
        resume_content = await generate_resume(
            profile=request.profile,
            job_description_text=request.job_description_text,
            jd_keywords=jd_data.keywords,
        )

        # Step 3: Render and compile LaTeX
        result = await render_and_compile(
            resume_data=resume_content,
            template_id=request.template_id,
        )

        job_id = result["job_id"]

        return GenerateResponse(
            success=True,
            message=(
                "Resume generated successfully!"
                if result["success"]
                else "Resume content generated. LaTeX compilation failed — .tex file is still available."
            ),
            job_id=job_id,
            pdf_available=result["success"],
            tex_available=True,
            download_url_pdf=f"/api/download/{job_id}/pdf" if result["success"] else None,
            download_url_tex=f"/api/download/{job_id}/tex",
            compilation_error=result.get("error"),
        )

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Resume generation failed: {str(e)}",
        )


@router.get("/download/{job_id}/{file_type}")
async def download_generated_file(job_id: str, file_type: str):
    """
    Download a generated resume file (PDF or .tex source).

    Args:
        job_id:    The generation job ID (from the generate response).
        file_type: Either 'pdf' or 'tex'.

    Returns:
        File download response.

    Raises:
        400: If file_type is not 'pdf' or 'tex'.
        404: If the file does not exist.
    """
    if file_type not in ("pdf", "tex"):
        raise HTTPException(
            status_code=400,
            detail="file_type must be 'pdf' or 'tex'.",
        )

    file_name = f"resume.{file_type}"
    file_path = GENERATED_DIR / job_id / file_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_name}. It may not have been generated.",
        )

    media_type = (
        "application/pdf" if file_type == "pdf"
        else "application/x-tex"
    )

    return FileResponse(
        path=str(file_path),
        filename=f"resume_{job_id[:8]}.{file_type}",
        media_type=media_type,
    )
