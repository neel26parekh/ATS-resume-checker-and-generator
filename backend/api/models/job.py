"""
Job Description Data Models
============================
Pydantic schemas for job description analysis — the structured data
extracted from a raw JD text using the Gemini AI.
"""

from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """
    Structured representation of a job description after AI analysis.

    Attributes:
        title:              Job title (e.g., "Senior Software Engineer").
        company:            Company name (if detected).
        required_skills:    Must-have skills listed in the JD.
        preferred_skills:   Nice-to-have / preferred skills.
        experience_level:   Required experience (e.g., "3-5 years", "Senior").
        education:          Education requirements (e.g., "BS in Computer Science").
        responsibilities:   Key job responsibilities.
        industry:           Detected industry/domain (e.g., "FinTech", "Healthcare").
        keywords:           All important keywords for ATS matching.
    """
    title: str = Field(default="", description="Job title")
    company: str = Field(default="", description="Company name")
    required_skills: list[str] = Field(default_factory=list, description="Must-have skills")
    preferred_skills: list[str] = Field(default_factory=list, description="Nice-to-have skills")
    experience_level: str = Field(default="", description="Required experience level")
    education: str = Field(default="", description="Education requirements")
    responsibilities: list[str] = Field(default_factory=list, description="Key responsibilities")
    industry: str = Field(default="", description="Industry or domain")
    keywords: list[str] = Field(default_factory=list, description="Important ATS keywords")


class JobAnalysisRequest(BaseModel):
    """Request body for the JD analysis endpoint."""
    job_description_text: str = Field(..., description="Raw job description text to analyze")


class JobAnalysisResponse(BaseModel):
    """
    Response from the JD analysis endpoint.

    Attributes:
        success:         Whether analysis succeeded.
        message:         Human-readable status message.
        job_description: Structured JD data (None if analysis failed).
    """
    success: bool = Field(..., description="Whether analysis succeeded")
    message: str = Field(..., description="Status message")
    job_description: JobDescription | None = Field(None, description="Structured JD data")
