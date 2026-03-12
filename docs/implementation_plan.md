# Phase 1 Implementation Plan — ATS Resume Checker & Generator

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| AI Provider | **Google Gemini** (free tier) | Free, powerful, user has experience with it |
| Authentication | **None** (prototype) | Keep MVP simple, add in Phase 2 |
| Database | **None** (prototype) | In-memory / file-based for MVP, add DB in Phase 2 |
| LaTeX Compiler | **tectonic** or **pdflatex** | tectonic is a single binary, easier to install |
| Frontend Framework | **React + Vite** | Fast dev server, modern tooling |
| Routing | **React Router v6** | Industry standard for React |

---

## Project Directory Structure

```
ats-resume-checker/
├── README.md                           # Project overview & setup guide
├── .gitignore
├── .env.example                        # Environment variable template
│
├── backend/
│   ├── requirements.txt                # Python dependencies
│   ├── config.py                       # Centralized configuration
│   ├── main.py                         # FastAPI app entry point
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── resume.py               # Resume data schemas
│   │   │   ├── job.py                  # Job description schemas
│   │   │   └── score.py                # Score response schemas
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py               # Health check endpoint
│   │       ├── resume.py               # Resume upload & parse
│   │       ├── scoring.py              # ATS scoring endpoint
│   │       └── generation.py           # Resume generation endpoint
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── resume_parser.py            # PDF/DOCX text extraction
│   │   ├── jd_analyzer.py              # Job description analysis via AI
│   │   ├── scoring_engine.py           # 7-dimension ATS scoring
│   │   ├── suggestion_engine.py        # Improvement suggestions
│   │   ├── resume_generator.py         # AI-powered resume content generation
│   │   └── latex_compiler.py           # LaTeX → PDF compilation
│   │
│   ├── templates/
│   │   └── latex/
│   │       ├── jake_resume.tex.j2      # Jake's Resume Jinja2 template
│   │       └── modern_professional.tex.j2  # Modern Professional template
│   │
│   └── utils/
│       ├── __init__.py
│       ├── text_processing.py          # Text cleaning, tokenization
│       └── file_handling.py            # File upload/download helpers
│
├── docs/
│   ├── project_proposal.md             # Full project proposal
│   ├── implementation_plan.md          # This file
│   ├── task.md                         # Task tracker
│   └── walkthrough.md                  # Build walkthrough
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx                    # React entry point
        ├── App.jsx                     # App shell with routing
        ├── index.css                   # Global design system
        ├── components/
        │   ├── Header.jsx              # Navigation bar
        │   ├── Header.css
        │   ├── FileUploader.jsx        # Drag & drop file upload
        │   ├── FileUploader.css
        │   ├── ScoreReport.jsx         # Score breakdown display
        │   ├── ScoreReport.css
        │   ├── RadarChart.jsx          # Canvas-based radar chart
        │   ├── RadarChart.css
        │   ├── SuggestionPanel.jsx     # Improvement suggestions
        │   └── SuggestionPanel.css
        └── pages/
            ├── HomePage.jsx            # Landing page
            ├── HomePage.css
            ├── CheckerPage.jsx         # ATS checker page
            ├── CheckerPage.css
            ├── GeneratorPage.jsx       # Resume generator page
            └── GeneratorPage.css
```

---

## Proposed Changes

### Backend — Configuration & Entry Point

#### [NEW] config.py
- Centralized config using environment variables
- Gemini API key, upload directory, LaTeX compiler path, CORS origins

#### [NEW] main.py
- FastAPI app with CORS middleware
- Router registration for all API route modules
- Startup events for temp directory creation

---

### Backend — API Models

#### [NEW] api/models/resume.py
- `ResumeData` — parsed resume sections (contact, summary, experience, education, skills)
- `ResumeUploadResponse` — parse result with extracted text + detected sections

#### [NEW] api/models/job.py
- `JobDescription` — structured JD data (required skills, preferred skills, experience level)
- `JobAnalysisResponse` — analyzed JD with categorized requirements

#### [NEW] api/models/score.py
- `ScoreDimension` — individual dimension score (name, score, max, weight, details)
- `ATSScoreReport` — full score report with overall score, dimensions, suggestions

---

### Backend — Core Services

#### [NEW] services/resume_parser.py
- `parse_pdf()` — Extract text from PDF using PyMuPDF
- `parse_docx()` — Extract text from DOCX using python-docx
- `extract_sections()` — Detect resume sections (contact, experience, education, skills)
- `detect_formatting_issues()` — Check for ATS-unfriendly elements

#### [NEW] services/jd_analyzer.py
- `analyze_job_description()` — Uses Gemini API to extract structured data from JD text
- Returns required skills, preferred skills, experience level, education requirements, industry

#### [NEW] services/scoring_engine.py
- `calculate_ats_score()` — Main scoring function with 7 dimensions
- `score_keyword_match()` — Exact + fuzzy keyword matching (30% weight)
- `score_skill_relevance()` — Semantic similarity via Gemini (20% weight)
- `score_experience_alignment()` — Experience level match (15% weight)
- `score_education_match()` — Education requirements match (10% weight)
- `score_formatting()` — ATS-parsability check (10% weight)
- `score_section_completeness()` — Section presence check (10% weight)
- `score_action_verbs()` — Action verb and quantification check (5% weight)

#### [NEW] services/suggestion_engine.py
- `generate_suggestions()` — Produces actionable improvement suggestions
- Uses score breakdown + JD analysis to suggest specific keyword additions, section reordering, quantification

#### [NEW] services/resume_generator.py
- `generate_resume_content()` — Uses Gemini to create tailored resume content
- Takes user profile + JD, returns structured resume data optimized for ATS
- Weaves JD keywords naturally into experience descriptions

#### [NEW] services/latex_compiler.py
- `render_latex()` — Fill Jinja2 LaTeX template with resume data
- `compile_to_pdf()` — Call pdflatex/tectonic to compile .tex → .pdf
- `cleanup_temp_files()` — Remove intermediate LaTeX files

---

### Backend — LaTeX Templates

#### [NEW] templates/latex/jake_resume.tex.j2
- Clean, single-column, ATS-optimized LaTeX template
- Based on Jake's Resume format (widely used in tech)
- Jinja2 variables for all resume sections

#### [NEW] templates/latex/modern_professional.tex.j2
- Professional template suitable for all industries
- Minimal design, maximum readability

---

### Backend — API Routes

#### [NEW] api/routes/health.py
- `GET /api/health` — Health check with service status

#### [NEW] api/routes/resume.py
- `POST /api/resume/parse` — Upload and parse a resume file (PDF/DOCX)

#### [NEW] api/routes/scoring.py
- `POST /api/score` — Score a resume against a job description

#### [NEW] api/routes/generation.py
- `POST /api/generate` — Generate a tailored resume (returns PDF + .tex)

---

## Verification Plan

### Automated Tests (via curl)
1. **Health check**: `curl http://localhost:8000/api/health` — expect `{"status": "healthy"}`
2. **Resume parse**: `curl -X POST -F "file=@test_resume.pdf" http://localhost:8000/api/resume/parse` — expect parsed sections
3. **ATS score**: `curl -X POST -H "Content-Type: application/json" -d '{"resume_text": "...", "job_description": "..."}' http://localhost:8000/api/score` — expect score breakdown
4. **Resume generate**: `curl -X POST -H "Content-Type: application/json" -d '{"profile": {...}, "job_description": "..."}' http://localhost:8000/api/generate` — expect PDF download

### Browser Testing
5. **Frontend UI walkthrough**: Open `http://localhost:5173`, verify all 3 pages load, navigation works, dark theme renders correctly
6. **End-to-end checker flow**: Upload a resume PDF, paste a JD, click "Check" → verify score report appears with radar chart
7. **End-to-end generator flow**: Fill profile form, paste JD, select template, click "Generate" → verify PDF downloads

### Manual Verification (User)
8. Open the downloaded PDF in a PDF reader and verify it looks professional and text is selectable (ATS-readable)
9. Try uploading different resume formats (PDF, DOCX) and verify both parse correctly
