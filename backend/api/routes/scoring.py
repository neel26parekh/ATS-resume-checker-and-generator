"""
Scoring Routes
==============
Endpoints for ATS score calculation — the core feature of the application.

Endpoints:
    POST /api/score          — Score a resume against a job description.
    POST /api/analyze-jd     — Analyze a job description (standalone).
"""

import asyncio

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel, Field

from api.models.score import ScoreRequest, ATSScoreReport
from api.models.job import JobAnalysisRequest, JobAnalysisResponse
from api.models.resume import ResumeData
from services.jd_analyzer import analyze_job_description, _analyze_job_description_fallback
from services.scoring_engine import calculate_ats_score
from services.suggestion_engine import generate_detailed_suggestions
from services.resume_parser import _detect_sections, _extract_contact_info, _extract_skills_from_sections
from utils.text_processing import clean_text


class SuggestionsRequest(BaseModel):
    """Request body for /api/suggestions — accepts the already-computed score report."""
    score_report: ATSScoreReport = Field(..., description="Score report from /api/score")
    job_description_text: str = Field(..., description="Raw job description text")
    resume_text: str = Field(..., description="Raw resume text")

router = APIRouter()


@router.post("/score", response_model=ATSScoreReport)
async def score_resume(request: ScoreRequest):
    """
    Score a resume against a job description.

    This is the primary endpoint. It:
    1. Analyzes the job description using AI
    2. Parses the resume text into sections
    3. Runs the 7-dimension scoring algorithm
    4. Generates improvement suggestions

    Args:
        request: ScoreRequest with resume_text and job_description_text.

    Returns:
        ATSScoreReport with score breakdown, suggestions, and keyword analysis.

    Raises:
        400: If required fields are empty.
        500: If scoring fails.
    """
    # Validate inputs
    if not request.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required.")
    if not request.job_description_text.strip():
        raise HTTPException(status_code=400, detail="Job description text is required.")

    # Shared local parser used in normal and fallback paths.
    def _parse_resume():
        cleaned_text = clean_text(request.resume_text)
        sections = _detect_sections(cleaned_text)
        contact_info = _extract_contact_info(cleaned_text)
        detected_skills = _extract_skills_from_sections(sections)
        return cleaned_text, sections, contact_info, detected_skills

    try:
        # Parse resume and analyze JD concurrently. If JD analysis is slow/rate-limited,
        # force a quick deterministic fallback so users still get a score fast.
        loop = asyncio.get_running_loop()
        parse_future = loop.run_in_executor(None, _parse_resume)
        jd_task = asyncio.create_task(analyze_job_description(request.job_description_text))

        cleaned_text, sections, contact_info, detected_skills = await parse_future

        try:
            job_description = await asyncio.wait_for(jd_task, timeout=12)
        except asyncio.TimeoutError:
            jd_task.cancel()
            print("WARNING: JD analysis timed out. Using fallback analyzer.")
            job_description = _analyze_job_description_fallback(request.job_description_text)
        except Exception as jd_error:
            jd_msg = str(jd_error).lower()
            if "429" in jd_msg or "quota" in jd_msg or "exhausted" in jd_msg:
                print("WARNING: JD analysis rate-limited. Using fallback analyzer.")
                job_description = _analyze_job_description_fallback(request.job_description_text)
            else:
                raise

        resume_data = ResumeData(
            raw_text=cleaned_text,
            sections=sections,
            contact_info=contact_info,
            detected_skills=detected_skills,
            formatting_issues=[],  # No file-level formatting issues for raw text
            file_type="text",
        )

        # Step 3: Calculate ATS score (pure Python, fast)
        score_report = await calculate_ats_score(resume_data, job_description)

        # Return immediately — suggestions are fetched separately via /api/suggestions
        return score_report

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        import traceback
        print("DEBUG: SCORING FAILED WITH EXCEPTION:")
        traceback.print_exc()
        
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
            # Route-level safety net: return score using deterministic JD fallback.
            print("WARNING: AI rate-limited in /score route. Using fallback JD analysis.")
            cleaned_text, sections, contact_info, detected_skills = _parse_resume()
            resume_data = ResumeData(
                raw_text=cleaned_text,
                sections=sections,
                contact_info=contact_info,
                detected_skills=detected_skills,
                formatting_issues=[],
                file_type="text",
            )
            jd_fallback = _analyze_job_description_fallback(request.job_description_text)
            score_report = await calculate_ats_score(resume_data, jd_fallback)
            return score_report

        raise HTTPException(
            status_code=500,
            detail=f"Scoring failed: {str(e)}",
        )


@router.post("/suggestions", response_model=list)
async def get_suggestions(request: SuggestionsRequest):
    """
    Generate AI improvement suggestions using the already-computed score report.

    Accepts the score report directly from the frontend — no re-analysis needed.
    Only makes a single AI call (suggestion generation).
    """
    try:
        suggestions = await generate_detailed_suggestions(
            request.score_report,
            request.job_description_text,
            request.resume_text,
        )
        return [s.model_dump() for s in suggestions]

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
            raise HTTPException(status_code=429, detail="AI API Rate Limit Exceeded. Please wait a minute and try again.")
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")


@router.post("/analyze-jd", response_model=JobAnalysisResponse)
async def analyze_jd_endpoint(request: JobAnalysisRequest):
    """
    Analyze a job description and return structured data.

    Standalone endpoint for previewing JD analysis results
    without running the full scoring pipeline.

    Args:
        request: JobAnalysisRequest with job_description_text.

    Returns:
        JobAnalysisResponse with structured JD data.
    """
    if not request.job_description_text.strip():
        raise HTTPException(status_code=400, detail="Job description text is required.")

    try:
        jd = await analyze_job_description(request.job_description_text)
        return JobAnalysisResponse(
            success=True,
            message="Job description analyzed successfully.",
            job_description=jd,
        )

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="AI API Rate Limit Exceeded. Please wait a minute and try again."
            )
            
        raise HTTPException(
            status_code=500,
            detail=f"JD analysis failed: {str(e)}",
        )
