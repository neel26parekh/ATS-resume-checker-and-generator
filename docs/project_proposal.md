# 🎯 ATS Resume Checker & Generator — Project Proposal

## What is This Project?

An **end-to-end ATS (Applicant Tracking System) Resume Platform** that helps job seekers:

1. **Check** if their resume/CV is ATS-friendly
2. **Score** their resume against a specific job description
3. **Generate** optimized resumes tailored to specific jobs
4. **Improve** their existing resume with actionable suggestions

> [!IMPORTANT]
> This is not just a simple keyword matcher. We're building an **intelligent platform** that understands context, industry norms, and what actually gets resumes past ATS filters and into human hands.

---

## 🧠 Deep Dive: What is ATS & Why Does it Matter?

Most companies (over 98% of Fortune 500) use Applicant Tracking Systems to filter resumes before a human ever sees them. These systems:

- **Parse** resumes into structured data (name, skills, experience, education)
- **Rank** candidates by matching keywords, skills, and qualifications against the job description
- **Filter out** resumes with poor formatting, missing sections, or low relevance scores

**The Problem**: Many qualified candidates get rejected because their resume isn't optimized for ATS systems — wrong formatting, missing keywords, poor structure.

**Our Solution**: A tool that acts as both a **diagnostic** (tells you what's wrong) and a **generative** tool (creates ATS-optimized resumes for you).

---

## 🚀 Core Features (MVP — Phase 1)

### 1. Resume Parser & ATS Compatibility Check
| Check | Description |
|-------|-------------|
| **Format Analysis** | Detects problematic elements (tables, images, headers/footers, columns, text boxes) |
| **Section Detection** | Verifies presence of critical sections (Contact, Summary, Experience, Education, Skills) |
| **File Format Check** | Warns about non-ATS-friendly formats (.png, .jpg) and recommends .pdf or .docx |
| **Font & Encoding** | Checks for unusual fonts or encoding that ATS can't parse |
| **Date Formatting** | Validates consistent, parseable date formats |
| **Bullet Point Structure** | Checks for action verbs, quantified achievements |

### 2. Job Description Analyzer
- Extracts **required skills**, **preferred skills**, **experience level**, **education requirements**
- Identifies **hidden keywords** that ATS systems prioritize
- Categorizes requirements into **must-have** vs **nice-to-have**
- Detects **industry/domain** for context-aware scoring

### 3. ATS Score Engine (Resume ↔ Job Description Matching)
| Scoring Dimension | Weight | Description |
|---|---|---|
| **Keyword Match** | 30% | Hard skills, tools, technologies mentioned in JD found in resume |
| **Skill Relevance** | 20% | Semantic similarity — not just exact match but related skills |
| **Experience Alignment** | 15% | Years of experience, seniority level match |
| **Education Match** | 10% | Degree, field of study, certifications |
| **Formatting Score** | 10% | ATS-parsability of the document |
| **Section Completeness** | 10% | All critical sections present and well-structured |
| **Action Verb Usage** | 5% | Strong action verbs, quantified achievements |

**Output**: Overall score (0-100) with detailed breakdown per dimension + improvement suggestions.

### 4. AI-Powered Resume Generator (ATS-Optimized + LaTeX)
- Takes user's **profile data** (experience, skills, education, projects) + **job description**
- Generates a **tailored resume** optimized for that specific job
- **All generated resumes are ATS-friendly by design**:
  - Clean single-column layouts, no tables/graphics/text boxes
  - Standard section headings ATS systems expect
  - Keywords from the JD woven naturally into content
  - Proper date formatting, consistent structure
  - Machine-readable PDF output (no scanned images)
- **LaTeX-based output** — resumes are generated as `.tex` files, compiled to PDF:
  - Pixel-perfect, professional typography
  - Multiple LaTeX templates (Jake's Resume, AltaCV, ModernCV, Deedy)
  - Users can also download the `.tex` source to edit manually
- Uses **industry-appropriate language** and action verbs from the JD

### 5. Resume Improvement Suggestions
- Side-by-side comparison of **your resume** vs **ideal resume** for the job
- Specific, actionable suggestions like:
  - "Add **Python** and **Machine Learning** to your skills section"
  - "Quantify your achievement: Instead of 'improved sales', write 'increased sales by 23% in Q3 2024'"
  - "Move your **Technical Skills** section higher — this JD prioritizes technical competency"

---

## 🌟 Advanced Features (Phase 2 — Scalability)

### 6. Multi-Resume Management
- Save multiple versions of your resume (one per job type)
- Track which resume was sent to which company
- **Resume versioning** — compare changes over time

### 7. Job Description Database & Matching
- Paste a job URL → auto-extracts the JD
- **Job-Resume match suggestions** — "This resume is 87% match for this job"
- Save job descriptions for later comparison

### 8. Cover Letter Generator
- Auto-generates cover letters tailored to the job description
- Uses information from your resume for consistency
- Multiple tone options (formal, conversational, enthusiastic)

### 9. LinkedIn Profile Optimizer
- Analyzes your LinkedIn profile against industry standards
- Suggests improvements for ATS-like LinkedIn recruiter searches
- Generates LinkedIn summary from your resume data

### 10. Interview Prep Module
- Based on the JD, generates likely interview questions
- Suggests STAR-format answers using your resume experience
- Technical question predictions for relevant roles

### 11. Analytics Dashboard
- Track your resume scores over time
- See which keywords are trending in your industry
- Compare your profile against industry benchmarks

### 12. Batch Processing
- Upload multiple resumes → score all against one JD
- Upload one resume → score against multiple JDs
- Useful for career coaches, universities, HR teams

---

## 🏗️ Proposed Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│            Next.js / React + Vite                    │
│    ┌──────────┬──────────┬──────────┬──────────┐    │
│    │ Upload   │ ATS      │ Resume   │ Dashboard│    │
│    │ & Parse  │ Scorer   │ Builder  │ & History│    │
│    └──────────┴──────────┴──────────┴──────────┘    │
└────────────────────────┬────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────┴────────────────────────────┐
│                   BACKEND (Python FastAPI)            │
│  ┌─────────┬──────────┬───────────┬──────────────┐  │
│  │ Resume  │ JD       │ Scoring   │ Generation   │  │
│  │ Parser  │ Analyzer │ Engine    │ Engine       │  │
│  └─────────┴──────────┴───────────┴──────────────┘  │
│  ┌─────────────────────────────────────────────────┐ │
│  │              AI/NLP Layer                        │ │
│  │  OpenAI API / Google Gemini / Local LLM         │ │
│  │  spaCy / NLTK (for parsing)                     │ │
│  └─────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────┐
│                    DATA LAYER                        │
│  ┌──────────┬──────────┬───────────────────────┐    │
│  │ PostgreSQL│ Redis    │ S3 / Local Storage    │    │
│  │ (Users,  │ (Cache,  │ (Resume files,        │    │
│  │  Scores) │  Sessions)│  Templates)           │    │
│  └──────────┴──────────┴───────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Recommended Tech Stack

| Layer | Technology | Why? |
|-------|-----------|------|
| **Frontend** | React + Vite | Fast, modern, great DX, easy to scale |
| **Styling** | Vanilla CSS + CSS Variables | Full control, no framework lock-in |
| **Backend** | Python + FastAPI | Best ecosystem for NLP/AI, async support, auto-docs |
| **AI/LLM** | Google Gemini API (free tier) | Powerful, free tier available, great for generation |
| **Resume Parsing** | PyMuPDF + python-docx + pdfplumber | Extract text from PDF/DOCX reliably |
| **NLP** | spaCy + scikit-learn | Keyword extraction, similarity scoring, NER |
| **Database** | SQLite → PostgreSQL | Start simple, scale when needed |
| **Resume Output** | LaTeX (Jinja2 templates → `.tex` → PDF via `pdflatex`/`tectonic`) | ATS-friendly, professional-grade PDF resumes |
| **File Storage** | Local → S3 | Start local, move to cloud for scale |
| **Deployment** | Render / Railway / Docker | Easy deployment, same stack as your Cold Mail Generator |

---

## 📊 How the Scoring Algorithm Works

```
                    ┌──────────────┐
                    │  User Input  │
                    │ Resume + JD  │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐    ┌──────────▼──────────┐
     │  Resume Parser  │    │  JD Analyzer         │
     │  → Sections     │    │  → Required Skills   │
     │  → Skills       │    │  → Preferred Skills  │
     │  → Experience   │    │  → Experience Level  │
     │  → Education    │    │  → Education Reqs    │
     │  → Format Info  │    │  → Industry/Domain   │
     └────────┬────────┘    └──────────┬──────────┘
              │                        │
              └────────────┬───────────┘
                           │
                  ┌────────▼────────┐
                  │  Scoring Engine │
                  │                 │
                  │ 1. Keyword Match│
                  │ 2. Semantic Sim │
                  │ 3. Exp Alignment│
                  │ 4. Edu Match    │
                  │ 5. Format Score │
                  │ 6. Completeness │
                  │ 7. Action Verbs │
                  └────────┬────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐    ┌──────────▼──────────┐
     │  Score Report   │    │  Suggestions Engine  │
     │  → Overall: 73  │    │  → Add keywords X,Y  │
     │  → Breakdown    │    │  → Quantify item Z   │
     │  → Radar Chart  │    │  → Reorder sections  │
     └─────────────────┘    └─────────────────────┘
```

---

## 🎯 What Makes This Scalable?

1. **Microservice-ready**: Each module (parser, scorer, generator) is independent — can be split into microservices
2. **API-first**: Everything goes through REST APIs — can add mobile apps, Chrome extensions, integrations later
3. **Database-backed**: User data, scores, resume versions all persisted — analytics and ML possible
4. **AI-agnostic**: LLM layer is abstracted — can swap OpenAI for Gemini, Llama, or custom models
5. **Template system**: Resume templates are data-driven — easy to add new ones without code changes
6. **Multi-tenant ready**: User authentication from day one — can add teams, organizations later

---

## 🗺️ Implementation Roadmap

### Phase 1: Working Prototype (What we build now)
- [x] Project setup (Frontend + Backend)
- [x] Resume upload & parsing (PDF + DOCX)
- [x] Job description input & analysis
- [x] ATS scoring engine with 7-dimension scoring
- [x] Score report with visual breakdown (radar chart, progress bars)
- [x] Basic resume improvement suggestions
- [x] Simple resume generator (1-2 templates)
- [x] PDF export of generated resume
- [x] Clean, modern UI with dark mode

### Phase 2: Enhanced Features
- [ ] User accounts & authentication
- [ ] Resume history & versioning
- [ ] Multiple resume templates (5+)
- [ ] Cover letter generator
- [ ] Job URL auto-extraction
- [ ] Interview question generator

### Phase 3: Scale & Monetize
- [ ] Batch processing for HR/recruiters
- [ ] LinkedIn profile optimization
- [ ] Analytics dashboard
- [ ] API for third-party integrations
- [ ] Premium templates & features
- [ ] Team/organization accounts

---

## 💡 Unique Selling Points (vs Competitors)

| Feature | Our Tool | Jobscan | Resume.io | Zety |
|---------|----------|---------|-----------|------|
| ATS Score | ✅ Detailed 7-dimension | ✅ Basic | ❌ | ❌ |
| Resume Generation | ✅ AI-tailored to JD | ❌ | ✅ Generic | ✅ Generic |
| Free tier | ✅ Core features free | ❌ Paid | ❌ Paid | ❌ Paid |
| Open source / Self-host | ✅ | ❌ | ❌ | ❌ |
| Improvement suggestions | ✅ Specific & actionable | ✅ Basic | ❌ | ❌ |
| Interview prep | ✅ (Phase 2) | ❌ | ❌ | ❌ |
