"""
Text Processing Utilities
=========================
Helper functions for cleaning, tokenizing, and analyzing text content
extracted from resumes and job descriptions.
"""

import re
from collections import Counter


# ── Strong Action Verbs ─────────────────────────────────────────────────────
# Curated list of strong action verbs that ATS systems and recruiters prefer.
# Organized by category for easy maintenance.

ACTION_VERBS = {
    # Leadership & Management
    "led", "managed", "directed", "supervised", "coordinated", "oversaw",
    "mentored", "guided", "delegated", "orchestrated", "spearheaded",

    # Achievement & Results
    "achieved", "delivered", "exceeded", "improved", "increased", "reduced",
    "optimized", "streamlined", "accelerated", "maximized", "minimized",
    "boosted", "enhanced", "elevated", "transformed", "revolutionized",

    # Development & Creation
    "developed", "designed", "built", "created", "implemented", "engineered",
    "architected", "established", "launched", "initiated", "pioneered",
    "introduced", "formulated", "constructed", "produced", "invented",

    # Analysis & Research
    "analyzed", "evaluated", "assessed", "investigated", "researched",
    "diagnosed", "examined", "identified", "discovered", "measured",
    "quantified", "forecasted", "modeled", "tested", "validated",

    # Communication & Collaboration
    "presented", "communicated", "collaborated", "negotiated", "facilitated",
    "advocated", "influenced", "persuaded", "trained", "educated",

    # Technical & Operations
    "automated", "configured", "deployed", "integrated", "migrated",
    "maintained", "monitored", "resolved", "troubleshot", "debugged",
    "refactored", "scaled", "containerized", "provisioned",

    # Strategy & Planning
    "strategized", "planned", "prioritized", "organized", "budgeted",
    "forecasted", "conceptualized", "proposed", "recommended",
}


def clean_text(text: str) -> str:
    """
    Normalize raw text extracted from documents.

    Operations:
        1. Replace multiple whitespace characters with a single space.
        2. Strip leading/trailing whitespace.
        3. Remove non-printable characters (except newlines).

    Args:
        text: Raw text from a PDF or DOCX file.

    Returns:
        Cleaned text string.
    """
    # Remove non-printable chars (keep newlines and tabs)
    text = re.sub(r'[^\x20-\x7E\n\t]', ' ', text)
    # Collapse multiple spaces into one
    text = re.sub(r'[ \t]+', ' ', text)
    # Collapse multiple newlines into double newline (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_keywords(text: str, top_n: int = 30) -> list[str]:
    """
    Extract the most frequent meaningful words from text.

    Uses a basic approach: tokenize, filter stopwords, count frequency.
    This is used as a fallback when the AI-based extraction is unavailable.

    Args:
        text:  Input text to extract keywords from.
        top_n: Number of top keywords to return.

    Returns:
        List of keywords sorted by frequency (most frequent first).
    """
    # Simple tokenization: extract words with 3+ characters
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

    # Filter out common English stopwords
    stopwords = {
        "the", "and", "for", "are", "but", "not", "you", "all", "can",
        "her", "was", "one", "our", "out", "has", "have", "had", "will",
        "with", "this", "that", "from", "they", "been", "said", "each",
        "which", "their", "about", "would", "make", "like", "just", "over",
        "such", "take", "than", "them", "very", "some", "could", "into",
        "year", "also", "back", "after", "should", "work", "first", "well",
        "even", "where", "any", "these", "know", "most", "other", "then",
        "what", "when", "more", "may", "who", "how", "its",
    }
    filtered = [w for w in words if w not in stopwords]

    # Count and return top N
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(top_n)]


def count_action_verbs(text: str) -> dict:
    """
    Count how many strong action verbs appear in the text.

    Args:
        text: Resume text to analyze.

    Returns:
        Dictionary with:
            - 'count': Total number of action verbs found.
            - 'found': List of action verbs that were detected.
            - 'total_sentences': Approximate sentence count.
            - 'ratio': Ratio of sentences starting with action verbs.
    """
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    found_verbs = [w for w in words if w in ACTION_VERBS]
    unique_found = list(set(found_verbs))

    # Count approximate sentences (lines starting with bullet-like patterns)
    bullet_lines = re.findall(r'(?:^|\n)\s*(?:[•\-\*]|\d+\.)\s*\w', text)
    sentence_count = max(len(bullet_lines), 1)

    return {
        "count": len(found_verbs),
        "unique_count": len(unique_found),
        "found": sorted(unique_found),
        "total_bullet_points": sentence_count,
        "ratio": round(len(found_verbs) / sentence_count, 2),
    }


def detect_quantified_achievements(text: str) -> dict:
    """
    Detect quantified achievements in resume text (numbers, percentages, dollar amounts).

    ATS systems and recruiters strongly favor quantified impacts like:
    - "Increased revenue by 23%"
    - "Managed a team of 12 engineers"
    - "Reduced costs by $500K"

    Args:
        text: Resume text to analyze.

    Returns:
        Dictionary with count and examples of quantified achievements.
    """
    patterns = [
        r'\d+%',                          # Percentages: 23%, 150%
        r'\$[\d,]+[KMB]?',               # Dollar amounts: $500K, $1.2M
        r'\d+\+?\s*(?:years?|months?)',   # Duration: 5 years, 3+ months
        r'(?:team|group)\s*of\s*\d+',     # Team size: team of 12
        r'\d{1,3}(?:,\d{3})+',           # Large numbers: 1,000,000
    ]

    achievements = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        achievements.extend(matches)

    return {
        "count": len(achievements),
        "examples": achievements[:10],  # Return up to 10 examples
    }
