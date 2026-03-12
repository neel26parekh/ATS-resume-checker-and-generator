"""Resume generation endpoints for creating tailored resumes."""

import asyncio
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import GENERATED_DIR
from services.resume_generator import generate_resume
from services.latex_compiler import render_and_compile, get_available_templates

router = APIRouter()
_generation_lock = asyncio.Lock()


def _is_rate_limited(error: Exception) -> bool:
    msg = str(error).lower()
    return any(x in msg for x in ["429", "quota", "exhausted", "resource_exhausted", "rate limit"])


class GenerateRequest(BaseModel):
    """Request body for resume generation."""

    profile: dict = Field(
        ...,
        description="User profile data",
    )
    job_description_text: str = Field(
        ...,
        description="Raw job description text",
    )
    template_id: str = Field(
        default="jake_resume",
        description="LaTeX template ID",
    )


class GenerateResponse(BaseModel):
    """Response from resume generation endpoint."""

    success: bool
    message: str
    job_id: str | None = None
    pdf_available: bool = False
    tex_available: bool = True
    download_url_pdf: str | None = None
    download_url_tex: str | None = None
    compilation_error: str | None = None


@router.get("/templates")
async def list_templates():
    """List available LaTeX resume templates."""
    return {"templates": get_available_templates()}


@router.post("/generate", response_model=GenerateResponse)
async def generate_resume_endpoint(request: GenerateRequest):
    """Generate an ATS-optimized resume tailored to a job description.
    
    This endpoint retries automatically on rate limit errors.
    """
    if not request.profile:
        raise HTTPException(status_code=400, detail="Profile data is required.")
    if not request.job_description_text.strip():
        raise HTTPException(status_code=400, detail="Job description text is required.")

    # Serialize generation calls to reduce burst traffic against Gemini limits.
    # This prevents overlapping generate requests from repeatedly hitting quota.
    async with _generation_lock:
        last_error = None
        backoff_schedule = [30, 60, 90]  # total wait budget before final failure: 180s
        for attempt in range(1, len(backoff_schedule) + 2):
            try:
                resume_content = await generate_resume(
                    profile=request.profile,
                    job_description_text=request.job_description_text,
                    jd_keywords=None,
                )

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
                        else "Resume content generated. LaTeX compilation failed."
                    ),
                    job_id=job_id,
                    pdf_available=result["success"],
                    tex_available=True,
                    download_url_pdf=f"/api/download/{job_id}/pdf" if result["success"] else None,
                    download_url_tex=f"/api/download/{job_id}/tex",
                    compilation_error=result.get("error"),
                )

            except HTTPException:
                raise
            except RuntimeError as e:
                raise HTTPException(status_code=503, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                is_rate_limit = _is_rate_limited(e)

                if is_rate_limit and attempt <= len(backoff_schedule):
                    wait_secs = backoff_schedule[attempt - 1]
                    print(
                        f"Rate limit on generation attempt {attempt}/{len(backoff_schedule) + 1}. "
                        f"Waiting {wait_secs}s..."
                    )
                    await asyncio.sleep(wait_secs)
                    continue

                last_error = e

                if is_rate_limit:
                    raise HTTPException(
                        status_code=429,
                        detail="AI API Rate Limit. The server retried automatically but quota is still exhausted. Please wait 2 minutes and try again."
                    )
                raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=f"Generation failed after retries: {str(last_error)}"
        )


@router.get("/download/{job_id}/{file_type}")
async def download_generated_file(job_id: str, file_type: str):
    """Download a generated resume file (PDF or LaTeX source)."""
    if not re.fullmatch(r'[0-9a-f]{12}', job_id):
        raise HTTPException(status_code=400, detail="Invalid job_id.")

    if file_type not in ("pdf", "tex"):
        raise HTTPException(status_code=400, detail="file_type must be pdf or tex")

    file_name = f"resume.{file_type}"
    file_path = GENERATED_DIR / job_id / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_name}")

    media_type = "application/pdf" if file_type == "pdf" else "application/x-tex"

    return FileResponse(
        path=str(file_path),
        filename=f"resume_{job_id[:8]}.{file_type}",
        media_type=media_type,
    )
