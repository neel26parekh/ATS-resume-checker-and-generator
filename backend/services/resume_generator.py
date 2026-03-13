"""
Resume Generator Service
========================
Generates tailored, ATS-optimized resume content using Google Gemini AI.

Takes a user's profile data (experience, skills, education, projects) and
a job description, then generates resume content that:
    - Naturally incorporates JD keywords for ATS matching
    - Uses strong action verbs and quantified achievements
    - Follows industry-standard formatting and section ordering
    - Tailors language to the specific job and industry

The generated content is structured data (dict) that can be fed into
LaTeX templates for PDF generation.

Usage:
    from services.resume_generator import generate_resume

    resume_content = await generate_resume(profile, job_description_text)
"""

import json
import re
from collections.abc import Iterable

import google.generativeai as genai
import typing_extensions as typing

from config import settings

class ExperienceSchema(typing.TypedDict):
    title: str
    company: str
    location: str
    start_date: str
    end_date: str
    bullets: list[str]

class EducationSchema(typing.TypedDict):
    degree: str
    institution: str
    location: str
    graduation_date: str
    gpa: str
    honors: str

class SkillsSchema(typing.TypedDict):
    languages: list[str]
    frameworks: list[str]
    tools: list[str]
    other: list[str]

class ProjectSchema(typing.TypedDict):
    name: str
    technologies: str
    date: str
    bullets: list[str]

class CertificationSchema(typing.TypedDict):
    name: str
    issuer: str
    date: str

class ResumeSchema(typing.TypedDict):
    name: str
    email: str
    phone: str
    linkedin: str
    github: str
    location: str
    summary: str
    experience: list[ExperienceSchema]
    education: list[EducationSchema]
    skills: SkillsSchema
    projects: list[ProjectSchema]
    certifications: list[CertificationSchema]


# ── Resume Generation Prompt ────────────────────────────────────────────────

GENERATION_PROMPT = """
You are an expert resume writer specializing in ATS-optimized resumes. 
Create a professional resume tailored to the following job description.

USER PROFILE:
{profile_data}

TARGET JOB DESCRIPTION:
{job_description}

Generate a complete resume as a JSON object with EXACTLY this structure:
{{
    "name": "Full Name",
    "email": "email@example.com",
    "phone": "phone number",
    "linkedin": "linkedin.com/in/username",
    "github": "github.com/username (if relevant)",
    "location": "City, State",
    "summary": "A 2-3 sentence professional summary tailored to this job. Include key skills and experience level.",
    "experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "location": "City, State",
            "start_date": "Month Year",
            "end_date": "Month Year or Present",
            "bullets": [
                "Achievement-focused bullet starting with strong action verb. Include quantified results.",
                "Another bullet with measurable impact..."
            ]
        }}
    ],
    "education": [
        {{
            "degree": "Degree type and major (e.g., B.S. in Computer Science)",
            "institution": "University Name",
            "location": "City, State",
            "graduation_date": "Month Year",
            "gpa": "GPA (if above 3.5)",
            "honors": "Honors or relevant coursework (optional)"
        }}
    ],
    "skills": {{
        "languages": ["Programming languages"],
        "frameworks": ["Frameworks and libraries"],
        "tools": ["Developer tools and platforms"],
        "other": ["Other relevant skills, certifications, languages"]
    }},
    "projects": [
        {{
            "name": "Project Name",
            "technologies": "Tech stack used",
            "date": "Month Year",
            "bullets": [
                "What you built and its impact",
                "Key technical details"
            ]
        }}
    ],
    "certifications": [
        {{
            "name": "Certification Name",
            "issuer": "Issuing Organization",
            "date": "Month Year"
        }}
    ]
}}

CRITICAL RULES:
1. Every experience bullet MUST start with a strong action verb (Led, Developed, Optimized, etc.)
2. Include quantified achievements wherever possible (percentages, dollar amounts, team sizes)
3. Naturally incorporate these keywords from the JD: {keywords}
4. Keep the summary concise (2-3 sentences max)
5. Order experience reverse-chronologically
6. Only include information from the user profile — do NOT fabricate experience or skills
7. If the user didn't provide certain info (like projects), include an empty array
8. Make skills match what's in the JD as much as possible using the user's actual skills

Return ONLY the JSON object. No markdown, no explanation.
"""


# ── Public API ──────────────────────────────────────────────────────────────

async def generate_resume(
    profile: dict,
    job_description_text: str,
    jd_keywords: list[str] | None = None,
) -> dict:
    """
    Generate a complete, ATS-optimized resume tailored to a job description.

    Args:
        profile:              User's profile data (name, experience, skills, education).
        job_description_text: Raw job description text.
        jd_keywords:          Optional pre-extracted JD keywords.

    Returns:
        Dictionary containing all resume sections with tailored content.

    Raises:
        RuntimeError: If Gemini API is not configured.
        ValueError: If AI response cannot be parsed.
    """
    if not settings.is_gemini_configured:
        return generate_resume_fallback(profile, job_description_text)

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    # Format the profile data as readable text
    profile_text = _format_profile(profile)

    # Build keywords list
    keywords_str = ", ".join(jd_keywords[:20]) if jd_keywords else "extract from JD"

    prompt = GENERATION_PROMPT.format(
        profile_data=profile_text,
        job_description=job_description_text[:3000],
        keywords=keywords_str,
    )

    # Attempt 1
    try:
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ResumeSchema,
                temperature=0.2,
            )
        )
        response_text = response.text.strip()
        
        # Parse the JSON
        parsed_data = _parse_resume_response(response_text)
        return parsed_data
        
    except ValueError as e:
        print(f"DEBUG: Resume Generation AI parsing failed on Attempt 1. Retrying... Error: {e}")
        # Attempt 2: Higher temperature
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ResumeSchema,
                temperature=0.7,
            )
        )
        response_text = response.text.strip()
        
        # Parse the JSON
        parsed_data = _parse_resume_response(response_text)
        return parsed_data
    except Exception as e:
        err = str(e).lower()
        if "429" in err or "quota" in err or "exhausted" in err or "resource_exhausted" in err:
            print("WARNING: Resume generation rate-limited. Using fallback generator.")
            return generate_resume_fallback(profile, job_description_text)
        raise


def generate_resume_fallback(profile: dict, job_description_text: str) -> dict:
    """Generate a deterministic resume structure when AI is unavailable.

    This keeps /api/generate functional under quota/rate-limit failures.
    """
    jd_keywords = _extract_jd_keywords(job_description_text)

    name = str(profile.get("name", "")).strip()
    email = str(profile.get("email", "")).strip()
    phone = str(profile.get("phone", "")).strip()
    linkedin = str(profile.get("linkedin", "")).strip()
    github = str(profile.get("github", "")).strip()
    location = str(profile.get("location", "")).strip()

    # Build summary from available profile/JD data without fabrication.
    top_keywords = ", ".join(jd_keywords[:6])
    summary_parts = []
    if name:
        summary_parts.append(f"{name} is a results-focused professional")
    else:
        summary_parts.append("Results-focused professional")
    if top_keywords:
        summary_parts.append(f"with experience in {top_keywords}")
    summary_parts.append("seeking to contribute to this role")
    summary = " ".join(summary_parts) + "."

    experiences = []
    for exp in _as_list(profile.get("experience")):
        if not isinstance(exp, dict):
            continue
        desc = str(exp.get("description", "")).strip()
        bullets = _description_to_bullets(desc)
        if not bullets:
            bullets = ["Delivered responsibilities aligned with team and project goals."]
        experiences.append({
            "title": str(exp.get("title", "")).strip() or "Role",
            "company": str(exp.get("company", "")).strip() or "Company",
            "location": str(exp.get("location", "")).strip(),
            "start_date": str(exp.get("start_date", "")).strip(),
            "end_date": str(exp.get("end_date", "")).strip() or "Present",
            "bullets": bullets[:4],
        })

    education = []
    for edu in _as_list(profile.get("education")):
        if not isinstance(edu, dict):
            continue
        education.append({
            "degree": str(edu.get("degree", "")).strip(),
            "institution": str(edu.get("institution", "")).strip(),
            "location": str(edu.get("location", "")).strip(),
            "graduation_date": str(edu.get("graduation_date", "")).strip(),
            "gpa": str(edu.get("gpa", "")).strip(),
            "honors": str(edu.get("honors", "")).strip(),
        })

    raw_skills = profile.get("skills", [])
    all_skills = [s.strip() for s in _as_list(raw_skills) if str(s).strip()]
    skills = {
        "languages": all_skills[:6],
        "frameworks": all_skills[6:12],
        "tools": all_skills[12:18],
        "other": all_skills[18:] + jd_keywords[:6],
    }

    projects = []
    for proj in _as_list(profile.get("projects")):
        if not isinstance(proj, dict):
            continue
        pdesc = str(proj.get("description", "")).strip()
        projects.append({
            "name": str(proj.get("name", "")).strip() or "Project",
            "technologies": ", ".join(all_skills[:5]),
            "date": str(proj.get("date", "")).strip(),
            "bullets": _description_to_bullets(pdesc)[:3] or ["Built and delivered project outcomes."],
        })

    certs = []
    for cert in _as_list(profile.get("certifications")):
        cert_name = str(cert).strip()
        if cert_name:
            certs.append({"name": cert_name, "issuer": "", "date": ""})

    return _validate_resume_structure({
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "location": location,
        "summary": summary,
        "experience": experiences,
        "education": education,
        "skills": skills,
        "projects": projects,
        "certifications": certs,
    })


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def _extract_jd_keywords(jd_text: str) -> list[str]:
    tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\-\+\.]{2,}\b", jd_text.lower())
    stop = {
        "the", "and", "for", "with", "you", "are", "our", "will", "this", "that", "from",
        "your", "have", "not", "all", "job", "role", "team", "work", "years", "year",
        "required", "preferred", "nice", "must", "experience", "skills",
    }
    keywords = []
    for t in tokens:
        if t in stop or t.isdigit():
            continue
        if t not in keywords:
            keywords.append(t)
        if len(keywords) >= 20:
            break
    return keywords


def _description_to_bullets(text: str) -> list[str]:
    chunks = [c.strip() for c in re.split(r"[\n\.;]+", text) if c.strip()]
    bullets = []
    for c in chunks:
        if len(c) < 8:
            continue
        # Ensure bullet starts with capitalized action-like phrasing.
        line = c[0].upper() + c[1:]
        if not line.endswith("."):
            line += "."
        bullets.append(line)
    return bullets


# ── Profile Formatting ──────────────────────────────────────────────────────

def _format_profile(profile: dict) -> str:
    """
    Format a user profile dictionary into readable text for the AI prompt.

    Args:
        profile: User's profile data with keys like 'name', 'experience', etc.

    Returns:
        Formatted string representation of the profile.
    """
    parts = []

    # Basic info
    if profile.get("name"):
        parts.append(f"Name: {profile['name']}")
    if profile.get("email"):
        parts.append(f"Email: {profile['email']}")
    if profile.get("phone"):
        parts.append(f"Phone: {profile['phone']}")
    if profile.get("linkedin"):
        parts.append(f"LinkedIn: {profile['linkedin']}")
    if profile.get("github"):
        parts.append(f"GitHub: {profile['github']}")
    if profile.get("location"):
        parts.append(f"Location: {profile['location']}")

    # Experience
    if profile.get("experience"):
        parts.append("\nWork Experience:")
        for exp in profile["experience"]:
            parts.append(
                f"  - {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')} "
                f"({exp.get('start_date', '')} - {exp.get('end_date', '')})"
            )
            if exp.get("description"):
                parts.append(f"    {exp['description']}")

    # Education
    if profile.get("education"):
        parts.append("\nEducation:")
        for edu in profile["education"]:
            parts.append(
                f"  - {edu.get('degree', 'N/A')} from {edu.get('institution', 'N/A')} "
                f"({edu.get('graduation_date', '')})"
            )

    # Skills
    if profile.get("skills"):
        parts.append(f"\nSkills: {', '.join(profile['skills'])}")

    # Projects
    if profile.get("projects"):
        parts.append("\nProjects:")
        for proj in profile["projects"]:
            parts.append(f"  - {proj.get('name', 'N/A')}: {proj.get('description', '')}")

    # Certifications
    if profile.get("certifications"):
        parts.append(f"\nCertifications: {', '.join(profile['certifications'])}")

    return "\n".join(parts) if parts else "No profile data provided."


# ── Response Parsing ────────────────────────────────────────────────────────

def _parse_resume_response(response_text: str) -> dict:
    """
    Parse the AI-generated resume response into a Python dictionary.

    Handles common AI response formatting issues.

    Args:
        response_text: Raw text from Gemini API.

    Returns:
        Dictionary with structured resume data.

    Raises:
        ValueError: If the response cannot be parsed as valid JSON.
    """
    cleaned = response_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    try:
        data = json.loads(cleaned)
        return _validate_resume_structure(data)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse generated resume as JSON: {e}\n"
            f"Response excerpt: {response_text[:500]}"
        ) from e


def _validate_resume_structure(data: dict) -> dict:
    """
    Validate and fill in defaults for the generated resume structure.

    Ensures all required fields exist, even if the AI omitted some.

    Args:
        data: Raw parsed JSON from AI response.

    Returns:
        Validated dictionary with all required fields.
    """
    defaults = {
        "name": "",
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": "",
        "location": "",
        "summary": "",
        "experience": [],
        "education": [],
        "skills": {"languages": [], "frameworks": [], "tools": [], "other": []},
        "projects": [],
        "certifications": [],
    }

    # Merge with defaults (data takes precedence)
    for key, default_value in defaults.items():
        if key not in data:
            data[key] = default_value

    # Ensure skills is a dict with expected keys
    if isinstance(data["skills"], list):
        data["skills"] = {"other": data["skills"], "languages": [], "frameworks": [], "tools": []}
    elif isinstance(data["skills"], dict):
        for skill_key in ["languages", "frameworks", "tools", "other"]:
            if skill_key not in data["skills"]:
                data["skills"][skill_key] = []

    return data
