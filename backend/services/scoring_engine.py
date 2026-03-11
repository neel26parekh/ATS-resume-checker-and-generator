"""
ATS Scoring Engine
==================
The core scoring algorithm that evaluates a resume against a job description
across 7 dimensions. Each dimension is scored 0-100 and weighted to produce
an overall ATS compatibility score.

Scoring Dimensions:
    1. Keyword Match      (30%) — Hard skills, tools, technologies
    2. Skill Relevance    (20%) — Semantic similarity of skills
    3. Experience Align.  (15%) — Years / seniority level match
    4. Education Match    (10%) — Degree, field of study
    5. Formatting Score   (10%) — ATS-parsability of the document
    6. Section Complete.  (10%) — Required sections present
    7. Action Verb Usage  (5%)  — Strong verbs, quantified achievements

Usage:
    from services.scoring_engine import calculate_ats_score

    report = await calculate_ats_score(resume_data, job_description)
    print(f"Overall: {report.overall_score} ({report.grade})")
"""

import re

import google.generativeai as genai

from api.models.resume import ResumeData
from api.models.job import JobDescription
from api.models.score import ScoreDimension, ATSScoreReport, Suggestion
from config import settings
from utils.text_processing import count_action_verbs, detect_quantified_achievements


# ── Score Weights ───────────────────────────────────────────────────────────
# These weights determine the importance of each dimension in the final score.

DIMENSION_WEIGHTS = {
    "Keyword Match":          0.30,
    "Skill Relevance":        0.20,
    "Experience Alignment":   0.15,
    "Education Match":        0.10,
    "Formatting Score":       0.10,
    "Section Completeness":   0.10,
    "Action Verb Usage":      0.05,
}

# Required sections that every resume should have
REQUIRED_SECTIONS = {"Contact", "Summary", "Experience", "Education", "Skills"}

# Grade thresholds
GRADE_THRESHOLDS = [
    (95, "A+"), (90, "A"), (85, "B+"), (80, "B"),
    (75, "C+"), (70, "C"), (60, "D"), (0, "F"),
]


# ── Public API ──────────────────────────────────────────────────────────────

async def calculate_ats_score(
    resume_data: ResumeData,
    job_description: JobDescription,
) -> ATSScoreReport:
    """
    Calculate a comprehensive ATS score for a resume against a job description.

    Runs all 7 scoring dimensions independently, then combines them
    using weighted averages to produce the final score and grade.

    Args:
        resume_data:     Parsed resume data from the resume parser.
        job_description: Analyzed job description data from the JD analyzer.

    Returns:
        ATSScoreReport with overall score, grade, dimension breakdown,
        and improvement suggestions.
    """
    resume_text_lower = resume_data.raw_text.lower()
    resume_skills_lower = [s.lower() for s in resume_data.detected_skills]

    # ── Run all scoring dimensions ──────────────────────────────────────
    dimensions: list[ScoreDimension] = []

    # 1. Keyword Match (30%)
    keyword_result = _score_keyword_match(
        resume_text_lower, job_description.keywords
    )
    dimensions.append(keyword_result["dimension"])
    keywords_found = keyword_result["found"]
    keywords_missing = keyword_result["missing"]

    # 2. Skill Relevance (20%)
    dimensions.append(_score_skill_relevance(
        resume_skills_lower,
        job_description.required_skills,
        job_description.preferred_skills,
    ))

    # 3. Experience Alignment (15%)
    dimensions.append(_score_experience_alignment(
        resume_data.raw_text, job_description.experience_level
    ))

    # 4. Education Match (10%)
    dimensions.append(_score_education_match(
        resume_data.raw_text, job_description.education
    ))

    # 5. Formatting Score (10%)
    dimensions.append(_score_formatting(resume_data.formatting_issues))

    # 6. Section Completeness (10%)
    dimensions.append(_score_section_completeness(resume_data.sections))

    # 7. Action Verb Usage (5%)
    dimensions.append(_score_action_verbs(resume_data.raw_text))

    # ── Calculate overall weighted score ────────────────────────────────
    overall_score = sum(d.score * d.weight for d in dimensions)
    overall_score = round(overall_score, 1)

    # ── Determine grade ─────────────────────────────────────────────────
    grade = "F"
    for threshold, letter in GRADE_THRESHOLDS:
        if overall_score >= threshold:
            grade = letter
            break

    # ── Generate overall summary ────────────────────────────────────────
    summary = _generate_summary(overall_score, grade, dimensions)

    # ── Collect all suggestions from dimensions ─────────────────────────
    suggestions = _collect_suggestions(dimensions, keywords_missing, resume_data)

    return ATSScoreReport(
        overall_score=overall_score,
        grade=grade,
        dimensions=dimensions,
        suggestions=suggestions,
        summary=summary,
        keywords_found=keywords_found,
        keywords_missing=keywords_missing,
    )


# ── Dimension Scoring Functions ─────────────────────────────────────────────


def _score_keyword_match(
    resume_text_lower: str,
    jd_keywords: list[str],
) -> dict:
    """
    Score: What percentage of JD keywords appear in the resume?

    This is the most heavily weighted dimension (30%) because ATS systems
    primarily work by keyword matching.

    Args:
        resume_text_lower: Lowercased resume text.
        jd_keywords:       Keywords extracted from the JD.

    Returns:
        Dictionary with 'dimension' (ScoreDimension) and lists of
        'found' and 'missing' keywords.
    """
    if not jd_keywords:
        return {
            "dimension": ScoreDimension(
                name="Keyword Match",
                score=50,
                weight=DIMENSION_WEIGHTS["Keyword Match"],
                details="No keywords extracted from job description.",
                suggestions=["Ensure the job description is detailed enough."],
            ),
            "found": [],
            "missing": [],
        }

    found = []
    missing = []

    for keyword in jd_keywords:
        keyword_lower = keyword.lower()
        # Check for exact match or close match (with word boundaries)
        pattern = re.compile(r'\b' + re.escape(keyword_lower) + r'\b')
        if pattern.search(resume_text_lower):
            found.append(keyword)
        else:
            missing.append(keyword)

    total = len(jd_keywords)
    match_ratio = len(found) / total if total > 0 else 0
    score = round(match_ratio * 100, 1)

    # Build detail string
    details = (
        f"Found {len(found)}/{total} keywords from the job description. "
        f"Match rate: {match_ratio:.0%}."
    )

    suggestions = []
    if missing:
        top_missing = missing[:5]
        suggestions.append(
            f"Add these missing keywords to your resume: {', '.join(top_missing)}"
        )

    return {
        "dimension": ScoreDimension(
            name="Keyword Match",
            score=score,
            weight=DIMENSION_WEIGHTS["Keyword Match"],
            details=details,
            suggestions=suggestions,
        ),
        "found": found,
        "missing": missing,
    }


def _score_skill_relevance(
    resume_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
) -> ScoreDimension:
    """
    Score: How well do the resume's skills match the JD requirements?

    Scores required skills at 2x weight vs preferred skills.

    Args:
        resume_skills:    Skills detected in the resume (lowercased).
        required_skills:  Must-have skills from JD.
        preferred_skills: Nice-to-have skills from JD.

    Returns:
        ScoreDimension with skill relevance score.
    """
    if not required_skills and not preferred_skills:
        return ScoreDimension(
            name="Skill Relevance",
            score=50,
            weight=DIMENSION_WEIGHTS["Skill Relevance"],
            details="No skills extracted from job description.",
        )

    # Score required skills (worth 2x)
    required_matches = sum(
        1 for skill in required_skills
        if skill.lower() in resume_skills
        or any(skill.lower() in rs for rs in resume_skills)
    )

    # Score preferred skills (worth 1x)
    preferred_matches = sum(
        1 for skill in preferred_skills
        if skill.lower() in resume_skills
        or any(skill.lower() in rs for rs in resume_skills)
    )

    # Calculate weighted score
    total_weight = len(required_skills) * 2 + len(preferred_skills)
    achieved_weight = required_matches * 2 + preferred_matches

    score = round((achieved_weight / max(total_weight, 1)) * 100, 1)

    # Build suggestions
    suggestions = []
    missing_required = [
        s for s in required_skills
        if s.lower() not in resume_skills
        and not any(s.lower() in rs for rs in resume_skills)
    ]
    if missing_required:
        suggestions.append(
            f"Add these REQUIRED skills: {', '.join(missing_required[:5])}"
        )

    details = (
        f"Matched {required_matches}/{len(required_skills)} required skills "
        f"and {preferred_matches}/{len(preferred_skills)} preferred skills."
    )

    return ScoreDimension(
        name="Skill Relevance",
        score=score,
        weight=DIMENSION_WEIGHTS["Skill Relevance"],
        details=details,
        suggestions=suggestions,
    )


def _score_experience_alignment(
    resume_text: str,
    required_experience: str,
) -> ScoreDimension:
    """
    Score: Does the candidate's experience level match the JD requirements?

    Looks for years of experience and seniority indicators in both
    the resume and JD.

    Args:
        resume_text:          Full resume text.
        required_experience:  Experience requirement from JD (e.g., "5+ years").

    Returns:
        ScoreDimension with experience alignment score.
    """
    suggestions = []

    # Extract years from resume (look for patterns like "5 years", "3+ years")
    resume_years = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", resume_text, re.IGNORECASE)
    resume_max_years = max([int(y) for y in resume_years], default=0)

    # Extract years from JD requirement
    jd_years = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", required_experience, re.IGNORECASE)
    jd_required_years = min([int(y) for y in jd_years], default=0)

    if jd_required_years == 0:
        # Can't determine requirement — give neutral score
        return ScoreDimension(
            name="Experience Alignment",
            score=70,
            weight=DIMENSION_WEIGHTS["Experience Alignment"],
            details="Could not determine specific experience requirement from JD.",
            suggestions=["Ensure your experience years are clearly stated in your resume."],
        )

    # Score based on how close resume experience is to JD requirement
    if resume_max_years >= jd_required_years:
        score = 100.0
        details = (
            f"Your experience ({resume_max_years}+ years) meets or exceeds "
            f"the requirement ({jd_required_years}+ years)."
        )
    elif resume_max_years >= jd_required_years * 0.7:
        score = 75.0
        details = (
            f"Your experience ({resume_max_years} years) is close to "
            f"the requirement ({jd_required_years}+ years)."
        )
        suggestions.append(
            "Highlight relevant experience more prominently. "
            "Include related projects or freelance work."
        )
    elif resume_max_years > 0:
        ratio = resume_max_years / jd_required_years
        score = round(ratio * 70, 1)
        details = (
            f"Your experience ({resume_max_years} years) is below "
            f"the requirement ({jd_required_years}+ years)."
        )
        suggestions.append(
            "Consider emphasizing transferable experience from related roles."
        )
    else:
        score = 30.0
        details = "No specific experience duration found in your resume."
        suggestions.append(
            "Add years of experience to your resume. "
            "Include durations for each role (e.g., 'Jan 2020 – Present')."
        )

    return ScoreDimension(
        name="Experience Alignment",
        score=score,
        weight=DIMENSION_WEIGHTS["Experience Alignment"],
        details=details,
        suggestions=suggestions,
    )


def _score_education_match(
    resume_text: str,
    education_requirement: str,
) -> ScoreDimension:
    """
    Score: Does the resume meet the education requirements from the JD?

    Checks for degree types (BS, MS, PhD) and field of study matches.

    Args:
        resume_text:            Full resume text.
        education_requirement:  Education requirement from JD.

    Returns:
        ScoreDimension with education match score.
    """
    if not education_requirement:
        return ScoreDimension(
            name="Education Match",
            score=80,
            weight=DIMENSION_WEIGHTS["Education Match"],
            details="No specific education requirement found in JD.",
        )

    resume_lower = resume_text.lower()
    edu_lower = education_requirement.lower()

    score = 50.0  # Base score
    details_parts = []
    suggestions = []

    # Check for degree types
    degree_patterns = {
        "phd": (r"\bph\.?d\.?\b", 100),
        "master": (r"\b(?:m\.?s\.?|master(?:s|'s)?|mba)\b", 90),
        "bachelor": (r"\b(?:b\.?s\.?|b\.?a\.?|bachelor(?:s|'s)?)\b", 80),
        "associate": (r"\b(?:a\.?s\.?|a\.?a\.?|associate(?:s|'s)?)\b", 60),
    }

    resume_has_degree = False
    for degree_name, (pattern, degree_score) in degree_patterns.items():
        if re.search(pattern, resume_lower):
            resume_has_degree = True
            # Check if this degree level meets the JD requirement
            if degree_name in edu_lower or re.search(pattern, edu_lower):
                score = degree_score
                details_parts.append(f"Found matching degree level: {degree_name}")
            else:
                score = max(score, degree_score - 20)
                details_parts.append(f"Found {degree_name} degree in resume")

    if not resume_has_degree:
        score = 30.0
        details_parts.append("No recognizable degree found in resume")
        suggestions.append("Ensure your education section clearly lists your degree(s).")

    details = ". ".join(details_parts) if details_parts else "Education section analyzed."

    return ScoreDimension(
        name="Education Match",
        score=score,
        weight=DIMENSION_WEIGHTS["Education Match"],
        details=details,
        suggestions=suggestions,
    )


def _score_formatting(formatting_issues: list[str]) -> ScoreDimension:
    """
    Score: How ATS-friendly is the resume's formatting?

    Starts at 100 and deducts points for each formatting issue detected
    by the resume parser.

    Args:
        formatting_issues: List of formatting issues from the parser.

    Returns:
        ScoreDimension with formatting score.
    """
    if not formatting_issues:
        return ScoreDimension(
            name="Formatting Score",
            score=100,
            weight=DIMENSION_WEIGHTS["Formatting Score"],
            details="No formatting issues detected. Great job!",
        )

    # Deduct 15 points per issue, minimum score of 20
    deduction_per_issue = 15
    score = max(100 - len(formatting_issues) * deduction_per_issue, 20)

    details = f"Found {len(formatting_issues)} formatting issue(s)."
    suggestions = formatting_issues  # Each issue is already a suggestion

    return ScoreDimension(
        name="Formatting Score",
        score=float(score),
        weight=DIMENSION_WEIGHTS["Formatting Score"],
        details=details,
        suggestions=suggestions,
    )


def _score_section_completeness(sections: list) -> ScoreDimension:
    """
    Score: Are all required resume sections present?

    Checks for: Contact, Summary, Experience, Education, Skills.

    Args:
        sections: List of detected ResumeSection objects.

    Returns:
        ScoreDimension with section completeness score.
    """
    found_sections = {s.name for s in sections}
    missing = REQUIRED_SECTIONS - found_sections
    present = REQUIRED_SECTIONS & found_sections

    score = round((len(present) / len(REQUIRED_SECTIONS)) * 100, 1)

    details = f"Found {len(present)}/{len(REQUIRED_SECTIONS)} required sections."
    suggestions = []
    if missing:
        suggestions.append(
            f"Add these missing sections: {', '.join(sorted(missing))}"
        )

    return ScoreDimension(
        name="Section Completeness",
        score=score,
        weight=DIMENSION_WEIGHTS["Section Completeness"],
        details=details,
        suggestions=suggestions,
    )


def _score_action_verbs(resume_text: str) -> ScoreDimension:
    """
    Score: Does the resume use strong action verbs and quantified achievements?

    Combines action verb usage and quantified achievements into one score.

    Args:
        resume_text: Full resume text.

    Returns:
        ScoreDimension with action verb usage score.
    """
    verb_analysis = count_action_verbs(resume_text)
    quant_analysis = detect_quantified_achievements(resume_text)

    # Score action verbs (50% of this dimension)
    verb_score = min(verb_analysis["unique_count"] * 5, 100)

    # Score quantified achievements (50% of this dimension)
    quant_score = min(quant_analysis["count"] * 10, 100)

    combined_score = round((verb_score + quant_score) / 2, 1)

    details = (
        f"Found {verb_analysis['unique_count']} unique action verbs "
        f"and {quant_analysis['count']} quantified achievements."
    )

    suggestions = []
    if verb_analysis["unique_count"] < 10:
        suggestions.append(
            "Use more strong action verbs like: led, developed, optimized, "
            "implemented, increased, reduced, designed."
        )
    if quant_analysis["count"] < 3:
        suggestions.append(
            "Add more quantified achievements. Instead of 'improved performance', "
            "write 'improved performance by 40%'."
        )

    return ScoreDimension(
        name="Action Verb Usage",
        score=combined_score,
        weight=DIMENSION_WEIGHTS["Action Verb Usage"],
        details=details,
        suggestions=suggestions,
    )


# ── Utilities ───────────────────────────────────────────────────────────────

def _generate_summary(
    score: float, grade: str, dimensions: list[ScoreDimension]
) -> str:
    """Generate a human-readable overall assessment summary."""
    if score >= 90:
        tone = "Excellent! Your resume is highly optimized for ATS systems."
    elif score >= 75:
        tone = "Good job! Your resume is fairly ATS-friendly with room for improvement."
    elif score >= 60:
        tone = "Your resume needs some work to pass ATS filters consistently."
    else:
        tone = "Your resume likely won't pass most ATS systems. Significant improvements needed."

    # Find weakest dimension
    weakest = min(dimensions, key=lambda d: d.score)

    return (
        f"{tone} Overall score: {score}/100 (Grade: {grade}). "
        f"Weakest area: {weakest.name} ({weakest.score}/100)."
    )


def _collect_suggestions(
    dimensions: list[ScoreDimension],
    keywords_missing: list[str],
    resume_data: ResumeData,
) -> list[Suggestion]:
    """Collect and prioritize suggestions from all scoring dimensions."""
    suggestions: list[Suggestion] = []

    # High priority: Missing keywords
    if keywords_missing:
        top_missing = keywords_missing[:8]
        suggestions.append(Suggestion(
            category="Keywords",
            priority="high",
            message=(
                f"Add these important keywords to your resume: "
                f"{', '.join(top_missing)}"
            ),
        ))

    # Collect from each dimension
    priority_map = {
        "Keyword Match": "high",
        "Skill Relevance": "high",
        "Experience Alignment": "medium",
        "Education Match": "medium",
        "Formatting Score": "high",
        "Section Completeness": "high",
        "Action Verb Usage": "low",
    }

    for dim in dimensions:
        priority = priority_map.get(dim.name, "medium")
        for suggestion_text in dim.suggestions:
            suggestions.append(Suggestion(
                category=dim.name,
                priority=priority,
                message=suggestion_text,
            ))

    # Sort by priority (high first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: priority_order.get(s.priority, 1))

    return suggestions
