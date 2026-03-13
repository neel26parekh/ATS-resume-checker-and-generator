"""
Job Description Analyzer Service
==================================
Analyzes raw job description text using Google Gemini AI to extract
structured data: required skills, preferred skills, experience level,
education requirements, responsibilities, and ATS keywords.

This is a critical input for the scoring engine — the quality of JD
analysis directly impacts the accuracy of ATS scores.

Usage:
    from services.jd_analyzer import analyze_job_description

    jd_data = await analyze_job_description("We are looking for a Senior...")
    print(jd_data.required_skills)
"""

import asyncio
import json
import re

import google.generativeai as genai
import typing_extensions as typing

from config import settings

class JobDescriptionSchema(typing.TypedDict):
    title: str
    company: str
    required_skills: list[str]
    preferred_skills: list[str]
    experience_level: str
    education: str
    responsibilities: list[str]
    industry: str
    keywords: list[str]
from api.models.job import JobDescription


# Common technology and ATS terms for heuristic keyword extraction fallback.
COMMON_SKILLS = {
    "python", "java", "javascript", "typescript", "sql", "nosql", "react", "node", "fastapi",
    "django", "flask", "spring", "aws", "azure", "gcp", "docker", "kubernetes", "git",
    "ci/cd", "linux", "rest", "graphql", "pandas", "numpy", "scikit-learn", "tensorflow",
    "pytorch", "spark", "hadoop", "airflow", "tableau", "power bi", "excel", "communication",
    "leadership", "problem solving", "agile", "scrum", "microservices", "testing", "pytest",
    "unit testing", "integration testing", "data analysis", "machine learning", "nlp", "llm",
}


# ── Gemini Configuration ────────────────────────────────────────────────────

def _configure_gemini() -> genai.GenerativeModel:
    """
    Configure and return a Gemini generative model instance.

    Returns:
        Configured GenerativeModel for text generation.

    Raises:
        RuntimeError: If the Gemini API key is not configured.
    """
    if not settings.is_gemini_configured:
        raise RuntimeError(
            "Gemini API key is not configured. "
            "Set GEMINI_API_KEY in your .env file."
        )

    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-2.0-flash-lite")


# ── JD Analysis Prompt ──────────────────────────────────────────────────────
# This prompt is carefully engineered to produce consistent, structured output.

JD_ANALYSIS_PROMPT = """
You are an expert ATS (Applicant Tracking System) analyst. Analyze the following 
job description and extract structured information.

Return your analysis as a JSON object with EXACTLY these fields:
{{
    "title": "The job title",
    "company": "Company name (or empty string if not found)",
    "required_skills": ["list of must-have skills and technologies"],
    "preferred_skills": ["list of nice-to-have / preferred skills"],
    "experience_level": "Required experience (e.g., '3-5 years', 'Senior', 'Entry Level')",
    "education": "Education requirement (e.g., 'BS in Computer Science')",
    "responsibilities": ["list of key job responsibilities (top 5-8)"],
    "industry": "Industry or domain (e.g., 'FinTech', 'Healthcare', 'E-commerce')",
    "keywords": ["ALL important keywords an ATS would scan for, including skills, tools, methodologies, certifications"]
}}

Rules:
- Extract ONLY what is explicitly mentioned in the JD. Do not infer or add skills not mentioned.
- Keywords should include ALL terms an ATS would match: technical skills, soft skills, 
  tools, frameworks, methodologies, certifications, and industry-specific terms.
- Separate required vs preferred skills carefully. If the JD says "nice to have" or "preferred",
  put those in preferred_skills.
- Return ONLY the JSON object, nothing else. No markdown, no explanation.

JOB DESCRIPTION:
{job_description}
"""


# ── Public API ──────────────────────────────────────────────────────────────

async def analyze_job_description(jd_text: str) -> JobDescription:
    """
    Analyze a job description using Gemini AI and return structured data.

    This function sends the JD text to Gemini with a carefully engineered
    prompt, parses the JSON response, and returns a validated JobDescription.

    Args:
        jd_text: Raw job description text (copy-pasted from a job posting).

    Returns:
        JobDescription with structured data extracted from the JD.

    Raises:
        RuntimeError: If Gemini API is not configured.
        ValueError: If the AI response cannot be parsed as valid JSON.
    """
    if not jd_text.strip():
        return JobDescription()

    # If Gemini is unavailable, always use deterministic fallback so scoring still works.
    if not settings.is_gemini_configured:
        print("WARNING: Gemini not configured. Using fallback JD analyzer.")
        return _analyze_job_description_fallback(jd_text)

    model = _configure_gemini()
    prompt = JD_ANALYSIS_PROMPT.format(job_description=jd_text)

    # Retry up to 3 times with exponential backoff on rate limit errors
    for attempt in range(3):
        try:
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=JobDescriptionSchema,
                    temperature=0.2,
                )
            )
            parsed_data = _parse_ai_response(response.text.strip())
            return JobDescription(**parsed_data)
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "429" in err_str or "quota" in err_str or "exhausted" in err_str or "resource_exhausted" in err_str
            is_parse_error = isinstance(e, ValueError)
            if is_rate_limit and attempt < 2:
                wait = 5
                print(f"WARNING: Rate limit on JD analysis (attempt {attempt+1}). Retrying in {wait}s...")
                await asyncio.sleep(wait)
                continue
            if is_parse_error and attempt < 2:
                # Retry parse errors with higher temperature
                print(f"⚠️  Parse error on JD analysis (attempt {attempt+1}). Retrying...")
                try:
                    response = await model.generate_content_async(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            response_mime_type="application/json",
                            response_schema=JobDescriptionSchema,
                            temperature=0.7,
                        )
                    )
                    parsed_data = _parse_ai_response(response.text.strip())
                    return JobDescription(**parsed_data)
                except Exception:
                    pass
            # Last attempt failed: return fallback instead of failing the request.
            if attempt == 2:
                print("WARNING: Gemini JD analysis failed after retries. Using fallback analyzer.")
                return _analyze_job_description_fallback(jd_text)

    # Safety net; should not normally execute.
    return _analyze_job_description_fallback(jd_text)


def _analyze_job_description_fallback(jd_text: str) -> JobDescription:
    """
    Lightweight non-AI JD parser used when Gemini is unavailable or rate-limited.

    Goal: keep ATS scoring functional with best-effort extracted fields.
    """
    text = jd_text.strip()
    lowered = text.lower()

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Title: prefer explicit role-like first line, otherwise empty.
    title = ""
    for ln in lines[:8]:
        if any(word in ln.lower() for word in ["engineer", "developer", "analyst", "manager", "scientist", "designer", "specialist"]):
            title = ln[:120]
            break

    # Experience level extraction.
    exp_match = re.search(r"(\d+\+?\s*(?:years?|yrs?))", lowered)
    if exp_match:
        experience_level = exp_match.group(1)
    elif any(k in lowered for k in ["senior", "lead", "principal"]):
        experience_level = "Senior"
    elif any(k in lowered for k in ["entry", "junior", "associate", "intern"]):
        experience_level = "Entry Level"
    else:
        experience_level = ""

    # Education extraction.
    edu_match = re.search(r"((?:bachelor|master|phd|b\.s\.|m\.s\.|bs|ms)[^\n\r\.;]*)", lowered)
    education = edu_match.group(1).strip().title() if edu_match else ""

    # Required / preferred split using sentence-level heuristics.
    sentence_chunks = re.split(r"[\n\r\.]+", text)
    required_chunks = []
    preferred_chunks = []
    for chunk in sentence_chunks:
        c = chunk.strip()
        if not c:
            continue
        c_low = c.lower()
        if any(k in c_low for k in ["required", "must have", "minimum qualifications"]):
            required_chunks.append(c)
        elif any(k in c_low for k in ["preferred", "nice to have", "plus", "bonus"]):
            preferred_chunks.append(c)

    # Keyword extraction: known terms + frequent technical tokens.
    found_common = [s for s in COMMON_SKILLS if s in lowered]
    token_candidates = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\-\+\.]{2,}\b", text)
    token_counts = {}
    for tok in token_candidates:
        t = tok.lower()
        if t in {"the", "and", "for", "with", "you", "are", "our", "will", "this", "that", "from", "your", "have"}:
            continue
        if t.isdigit():
            continue
        token_counts[t] = token_counts.get(t, 0) + 1

    frequent_tokens = sorted(token_counts.items(), key=lambda x: x[1], reverse=True)
    frequent_keywords = [t for t, _ in frequent_tokens[:30]]

    keywords = []
    for kw in found_common + frequent_keywords:
        if kw not in keywords:
            keywords.append(kw)

    # Skills lists from keywords.
    required_skills = []
    preferred_skills = []
    for kw in keywords:
        if kw in COMMON_SKILLS:
            if any(kw in rc.lower() for rc in required_chunks):
                required_skills.append(kw)
            elif any(kw in pc.lower() for pc in preferred_chunks):
                preferred_skills.append(kw)

    # If buckets are empty, seed required from strongest detected skills.
    if not required_skills:
        required_skills = [kw for kw in keywords if kw in COMMON_SKILLS][:12]

    # Responsibilities: collect bullet-like lines with action verbs.
    responsibilities = []
    for ln in lines:
        l_low = ln.lower()
        if any(v in l_low for v in ["develop", "design", "build", "maintain", "lead", "analyze", "implement", "collaborate", "manage", "optimize"]):
            responsibilities.append(ln[:160])
        if len(responsibilities) >= 8:
            break

    return JobDescription(
        title=title,
        company="",
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        experience_level=experience_level,
        education=education,
        responsibilities=responsibilities,
        industry="",
        keywords=keywords[:50],
    )


async def extract_keywords_from_jd(jd_text: str) -> list[str]:
    """
    Quick keyword extraction from a JD — a lighter alternative to full analysis.

    Uses the full analyzer under the hood but returns only the keywords list.

    Args:
        jd_text: Raw job description text.

    Returns:
        List of ATS-relevant keywords from the JD.
    """
    jd_data = await analyze_job_description(jd_text)
    return jd_data.keywords


# ── Response Parsing ────────────────────────────────────────────────────────

def _parse_ai_response(response_text: str) -> dict:
    """
    Parse the AI response text into a Python dictionary.

    Handles common AI response quirks:
        - Markdown code block wrappers (```json ... ```)
        - Leading/trailing whitespace
        - Invalid JSON with trailing commas
        - Literal newline control characters inside strings

    Args:
        response_text: Raw text from the Gemini API response.

    Returns:
        Parsed dictionary from the JSON response.

    Raises:
        ValueError: If the response cannot be parsed as valid JSON.
    """
    # Strip markdown code block markers if present
    cleaned = response_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # Remove trailing commas (common AI mistake)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    
    # Protect against literal newlines inside JSON strings from AI
    def clean_strings(match):
        return match.group(0).replace('\n', ' ').replace('\r', '').replace('\t', ' ')
    
    cleaned = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', clean_strings, cleaned)

    try:
        # strict=False allows unescaped control characters just in case
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse AI response as JSON: {e}\n"
            f"Raw response:\n{response_text[:500]}"
        ) from e
