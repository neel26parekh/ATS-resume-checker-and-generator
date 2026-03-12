"""
Suggestion Engine
=================
Generates detailed, actionable improvement suggestions for a resume
based on the ATS score report and job description analysis.

Uses Gemini AI for context-aware suggestions that go beyond simple
keyword matching — providing specific wording improvements, section
reordering advice, and content enhancement tips.

Usage:
    from services.suggestion_engine import generate_detailed_suggestions

    suggestions = await generate_detailed_suggestions(score_report, jd, resume_text)
"""

import asyncio
import json
import re

import google.generativeai as genai
import typing_extensions as typing

from config import settings

class SuggestionSchema(typing.TypedDict):
    category: str
    priority: str
    message: str
from api.models.score import ATSScoreReport, Suggestion


# ── AI Suggestion Prompt ────────────────────────────────────────────────────

SUGGESTION_PROMPT = """
You are an expert resume coach and ATS optimization specialist. Based on the 
following analysis, provide specific, actionable suggestions to improve this resume.

CURRENT ATS SCORE: {overall_score}/100 (Grade: {grade})

DIMENSION SCORES:
{dimension_breakdown}

MISSING KEYWORDS: {missing_keywords}
FOUND KEYWORDS: {found_keywords}

JOB DESCRIPTION:
{job_description}

RESUME TEXT (first 2000 chars):
{resume_excerpt}

Provide 5-8 specific, actionable suggestions. For each suggestion, provide:
1. A specific change (not generic advice)
2. Example wording they could use
3. Which section to modify

Return as a JSON array with objects having these fields:
- "category": one of "Keywords", "Content", "Structure", "Formatting", "Impact"
- "priority": one of "high", "medium", "low"
- "message": the full suggestion with specific examples

Return ONLY the JSON array. No markdown, no explanation.
"""


# ── Public API ──────────────────────────────────────────────────────────────

async def generate_detailed_suggestions(
    score_report: ATSScoreReport,
    job_description_text: str,
    resume_text: str,
) -> list[Suggestion]:
    """
    Generate AI-powered detailed improvement suggestions.

    Combines the rule-based suggestions from the scoring engine with
    AI-generated context-aware suggestions for maximum helpfulness.

    Args:
        score_report:          The ATS score report from the scoring engine.
        job_description_text:  Original JD text for context.
        resume_text:           Original resume text for specific suggestions.

    Returns:
        List of prioritized Suggestion objects.
    """
    # Start with the rule-based suggestions from the score report
    all_suggestions = list(score_report.suggestions)

    # Add AI-generated suggestions if Gemini is configured
    if settings.is_gemini_configured:
        ai_suggestions = await _get_ai_suggestions(
            score_report, job_description_text, resume_text
        )
        all_suggestions.extend(ai_suggestions)

    # Deduplicate (by message similarity)
    unique_suggestions = _deduplicate_suggestions(all_suggestions)

    # Sort: high → medium → low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    unique_suggestions.sort(key=lambda s: priority_order.get(s.priority, 1))

    return unique_suggestions


# ── AI Suggestions ──────────────────────────────────────────────────────────

async def _get_ai_suggestions(
    score_report: ATSScoreReport,
    job_description_text: str,
    resume_text: str,
) -> list[Suggestion]:
    """
    Get context-aware suggestions from Gemini AI.

    Args:
        score_report:         The scoring report with dimension breakdown.
        job_description_text: Original JD text.
        resume_text:          Original resume text.

    Returns:
        List of AI-generated Suggestion objects.
    """
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")

        # Build dimension breakdown string
        dim_lines = [
            f"  - {d.name}: {d.score}/100 (weight: {d.weight:.0%})"
            for d in score_report.dimensions
        ]
        dimension_breakdown = "\n".join(dim_lines)

        prompt = SUGGESTION_PROMPT.format(
            overall_score=score_report.overall_score,
            grade=score_report.grade,
            dimension_breakdown=dimension_breakdown,
            missing_keywords=", ".join(score_report.keywords_missing[:15]),
            found_keywords=", ".join(score_report.keywords_found[:15]),
            job_description=job_description_text[:1500],
            resume_excerpt=resume_text[:2000],
        )

        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=list[SuggestionSchema],
                temperature=0.2,
            )
        )
        response_text = response.text.strip()

        return _parse_ai_suggestions(response_text)

    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "exhausted" in err_str or "resource_exhausted" in err_str:
            # One automatic retry after a short wait
            try:
                print("⚠️  Rate limit on suggestions. Waiting 15s then retrying...")
                await asyncio.sleep(15)
                response = await model.generate_content_async(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=list[SuggestionSchema],
                        temperature=0.2,
                    )
                )
                return _parse_ai_suggestions(response.text.strip())
            except Exception:
                pass
        # AI suggestions are a nice-to-have — don't fail the whole flow
        print(f"⚠️ AI suggestion generation failed: {e}")
        return []


def _parse_ai_suggestions(response_text: str) -> list[Suggestion]:
    """Parse AI response into Suggestion objects."""
    # Clean markdown wrappers
    cleaned = response_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # Protect against literal newlines inside JSON strings from AI
    def clean_strings(match):
        return match.group(0).replace('\n', ' ').replace('\r', '').replace('\t', ' ')
    
    cleaned = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', clean_strings, cleaned)

    try:
        items = json.loads(cleaned, strict=False)
        if not isinstance(items, list):
            return []

        suggestions = []
        for item in items:
            if isinstance(item, dict) and "message" in item:
                suggestions.append(Suggestion(
                    category=item.get("category", "General"),
                    priority=item.get("priority", "medium"),
                    message=item["message"],
                ))
        return suggestions

    except (json.JSONDecodeError, KeyError):
        return []


# ── Deduplication ───────────────────────────────────────────────────────────

def _deduplicate_suggestions(suggestions: list[Suggestion]) -> list[Suggestion]:
    """Remove duplicate or very similar suggestions."""
    seen_messages: set[str] = set()
    unique: list[Suggestion] = []

    for suggestion in suggestions:
        # Create a simplified key for comparison
        key = suggestion.message.lower()[:80]
        if key not in seen_messages:
            seen_messages.add(key)
            unique.append(suggestion)

    return unique
