"""
ATS Score Data Models
=====================
Pydantic schemas for the scoring engine output — includes individual
dimension scores, the full report, and the scoring request format.
"""

from pydantic import BaseModel, Field


class ScoreDimension(BaseModel):
    """
    Score for a single ATS dimension (e.g., 'Keyword Match').

    Attributes:
        name:       Dimension name (e.g., "Keyword Match").
        score:      Achieved score for this dimension (0-100 scale).
        max_score:  Maximum possible score (always 100).
        weight:     Weight of this dimension in the overall score (0.0-1.0).
        details:    Human-readable explanation of the score.
        suggestions: Specific improvement suggestions for this dimension.
    """
    name: str = Field(..., description="Dimension name")
    score: float = Field(..., ge=0, le=100, description="Score out of 100")
    max_score: float = Field(default=100, description="Maximum possible score")
    weight: float = Field(..., ge=0, le=1, description="Dimension weight (0.0 - 1.0)")
    details: str = Field(default="", description="Explanation of the score")
    suggestions: list[str] = Field(default_factory=list, description="Improvement tips")


class Suggestion(BaseModel):
    """
    An actionable improvement suggestion for the resume.

    Attributes:
        category:   Suggestion category (e.g., "Keywords", "Formatting").
        priority:   Priority level: "high", "medium", or "low".
        message:    The suggestion text.
    """
    category: str = Field(..., description="Suggestion category")
    priority: str = Field(..., description="Priority: high, medium, or low")
    message: str = Field(..., description="Actionable suggestion text")


class ATSScoreReport(BaseModel):
    """
    Complete ATS score report for a resume-JD combination.

    Attributes:
        overall_score:  Weighted overall ATS score (0-100).
        grade:          Letter grade (A+, A, B+, B, C+, C, D, F).
        dimensions:     Breakdown scores for each of the 7 dimensions.
        suggestions:    Prioritized list of improvement suggestions.
        summary:        Brief overall assessment text.
        keywords_found: JD keywords that were found in the resume.
        keywords_missing: JD keywords that are missing from the resume.
    """
    overall_score: float = Field(..., ge=0, le=100, description="Weighted overall score")
    grade: str = Field(..., description="Letter grade (A+ to F)")
    dimensions: list[ScoreDimension] = Field(..., description="Per-dimension score breakdown")
    suggestions: list[Suggestion] = Field(default_factory=list, description="Improvement suggestions")
    summary: str = Field(default="", description="Overall assessment summary")
    keywords_found: list[str] = Field(default_factory=list, description="Matched JD keywords")
    keywords_missing: list[str] = Field(default_factory=list, description="Missing JD keywords")


class ScoreRequest(BaseModel):
    """
    Request body for the ATS scoring endpoint.

    The client can provide either:
    - resume_text + job_description_text (both as strings), or
    - resume_data + job_description (pre-parsed structured data)
    """
    resume_text: str = Field(..., description="Raw text of the resume")
    job_description_text: str = Field(..., description="Raw text of the job description")
