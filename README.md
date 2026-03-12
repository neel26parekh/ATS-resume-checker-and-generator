# ATS Resume Checker & Generator

An end-to-end **AI-powered platform** for checking ATS (Applicant Tracking System) compatibility, scoring resumes against job descriptions, and generating optimized LaTeX resumes.

## ✨ Features

- **🔍 ATS Score Checker** — Upload your resume and get a detailed 7-dimension ATS compatibility score
- **📊 Visual Score Report** — Radar chart, progress bars, and keyword analysis
- **💡 AI-Powered Suggestions** — Specific, actionable improvements using Google Gemini
- **✨ Resume Generator** — Generate tailored, ATS-optimized resumes from your profile
- **📄 LaTeX PDF Output** — Professional typeset resumes with downloadable `.tex` source
- **🔑 Keyword Analysis** — See which JD keywords you hit and which you missed

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| AI | Google Gemini API |
| Resume Parsing | PyMuPDF + python-docx |
| Resume Output | LaTeX (Jinja2 → pdflatex) |

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Google Gemini API key** — [Get free key here](https://aistudio.google.com/apikey)
- **LaTeX** (optional, for PDF compilation) — `brew install mactex` or install [tectonic](https://tectonic-typesetting.github.io/)

### 1. Clone & Setup Environment

```bash
# Navigate to the project
cd ats-resume-checker

# Copy environment template and add your API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Start Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open the App

Visit **http://localhost:5173** in your browser.

## 🚢 Production Run (Single Server)

This project is configured so FastAPI serves both API + built frontend.

```bash
# from repo root
./start.sh start

# useful commands
./start.sh status
./start.sh logs
./start.sh restart
./start.sh stop
```

Open **http://localhost:8000**.

## ☁️ Deploy (Render via Docker)

This repo includes `Dockerfile` and `render.yaml` for direct deployment.

### Steps

1. Push this repository to GitHub.
2. In Render, create a new **Blueprint** service from this repo.
3. Add environment variable:
    - `GEMINI_API_KEY` = your Gemini key
4. Deploy.

Render will use:
- `render.yaml` for service config
- `Dockerfile` to build frontend + backend into one container
- Health check: `/api/health`

## ⚠️ Gemini Rate Limit Note (Free Tier)

- Free-tier Gemini can still return `429` during traffic spikes.
- The app now retries generation server-side with longer backoff and serialized requests.
- If quota is exhausted globally, users may still need to wait ~2 minutes and retry.

For production traffic, move to a higher Gemini quota tier.

## 📁 Project Structure

```
ats-resume-checker/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Configuration management
│   ├── api/
│   │   ├── models/              # Pydantic data schemas
│   │   │   ├── resume.py        # Resume parsing models
│   │   │   ├── job.py           # Job description models
│   │   │   └── score.py         # Score report models
│   │   └── routes/              # API endpoint handlers
│   │       ├── health.py        # Health check
│   │       ├── resume.py        # Resume upload & parse
│   │       ├── scoring.py       # ATS scoring
│   │       └── generation.py    # Resume generation
│   ├── services/                # Core business logic
│   │   ├── resume_parser.py     # PDF/DOCX text extraction
│   │   ├── jd_analyzer.py       # JD analysis via Gemini AI
│   │   ├── scoring_engine.py    # 7-dimension scoring algorithm
│   │   ├── suggestion_engine.py # Improvement suggestions
│   │   ├── resume_generator.py  # AI resume content generation
│   │   └── latex_compiler.py    # LaTeX template rendering & compilation
│   ├── templates/latex/         # Jinja2 LaTeX resume templates
│   └── utils/                   # Text processing & file handling
│
└── frontend/
    └── src/
        ├── components/          # Reusable UI components
        │   ├── Header.jsx       # Navigation bar
        │   ├── FileUploader.jsx # Drag & drop file upload
        │   ├── ScoreReport.jsx  # Score display with charts
        │   ├── RadarChart.jsx   # Custom canvas radar chart
        │   └── SuggestionPanel.jsx
        └── pages/               # App pages
            ├── HomePage.jsx     # Landing page
            ├── CheckerPage.jsx  # ATS score checker
            └── GeneratorPage.jsx # Resume generator
```

## 📊 Scoring Dimensions

| Dimension | Weight | Description |
|---|---|---|
| Keyword Match | 30% | JD keywords found in resume |
| Skill Relevance | 20% | Skills alignment with requirements |
| Experience Alignment | 15% | Experience level match |
| Education Match | 10% | Education requirements match |
| Formatting Score | 10% | ATS-parsability of the document |
| Section Completeness | 10% | Required sections present |
| Action Verb Usage | 5% | Strong verbs & quantified achievements |

## 📄 License

MIT License — Free to use, modify, and distribute.
