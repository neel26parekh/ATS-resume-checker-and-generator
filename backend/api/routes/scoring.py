"""
Scoring Routes
==============
Endpoints for ATS score calculation — the core feature of the application.

Endpoints:
    POST /api/score          — Score a resume against a job description.
    POST /api/analyze-jd     — Analyze a job description (standalone).
"""

from fastapi import APIRouter, HTTPException

from api.models.score import ScoreRequest, ATSScoreReport
from api.models.job import JobAnalysisRequest, JobAnalysisResponse
from api.models.resume import ResumeData
from services.jd_analyzer import analyze_job_description
from services.scoring_engine import calculate_ats_score
from services.suggestion_engine import generate_detailed_suggestions
from services.resume_parser import _detect_sections, _extract_contact_info, _extract_skills_from_sections
from utils.text_processing import clean_text

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

    try:
        # Step 1: Analyze the job description
        job_description = await analyze_job_description(request.job_description_text)

        # Step 2: Build ResumeData from raw text
        cleaned_text = clean_text(request.resume_text)
        sections = _detect_sections(cleaned_text)
        contact_info = _extract_contact_info(cleaned_text)
        detected_skills = _extract_skills_from_sections(sections)

        resume_data = ResumeData(
            raw_text=cleaned_text,
            sections=sections,
            contact_info=contact_info,
            detected_skills=detected_skills,
            formatting_issues=[],  # No file-level formatting issues for raw text
            file_type="text",
        )

        # Step 3: Calculate ATS score
        score_report = await calculate_ats_score(resume_data, job_description)

        # Step 4: Enhance with AI suggestions
        enhanced_suggestions = await generate_detailed_suggestions(
            score_report,
            request.job_description_text,
            request.resume_text,
        )
        score_report.suggestions = enhanced_suggestions

        return score_report

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scoring failed: {str(e)}",
        )


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
        raise HTTPException(
            status_code=500,
            detail=f"JD analysis failed: {str(e)}",
        )
