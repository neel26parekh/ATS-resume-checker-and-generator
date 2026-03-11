/**
 * HomePage — Landing Page
 * =======================
 * The first page users see. Features a hero section with animated gradient,
 * feature cards explaining what the app does, and CTA buttons.
 */

import { Link } from 'react-router-dom';
import './HomePage.css';

export default function HomePage() {
    return (
        <div className="home-page">
            {/* ── Hero Section ──────────────────────────────────────────── */}
            <section className="hero">
                <div className="hero-bg"></div>
                <div className="container hero-content">
                    <div className="hero-badge">🚀 AI-Powered Resume Platform</div>
                    <h1 className="hero-title">
                        Beat the <span className="gradient-text">ATS</span> &
                        Land Your <span className="gradient-text">Dream Job</span>
                    </h1>
                    <p className="hero-subtitle">
                        Check your resume's ATS compatibility, get a detailed score with
                        improvement suggestions, and generate tailored LaTeX resumes
                        optimized for any job description.
                    </p>
                    <div className="hero-actions">
                        <Link to="/checker" className="btn btn-primary btn-lg">
                            🔍 Check My Resume
                        </Link>
                        <Link to="/generator" className="btn btn-secondary btn-lg">
                            ✨ Generate Resume
                        </Link>
                    </div>
                    <div className="hero-stats">
                        <div className="stat">
                            <span className="stat-number">7</span>
                            <span className="stat-label">Scoring Dimensions</span>
                        </div>
                        <div className="stat-divider" />
                        <div className="stat">
                            <span className="stat-number">AI</span>
                            <span className="stat-label">Powered Analysis</span>
                        </div>
                        <div className="stat-divider" />
                        <div className="stat">
                            <span className="stat-number">LaTeX</span>
                            <span className="stat-label">PDF Output</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── Features Section ──────────────────────────────────────── */}
            <section className="features container">
                <h2 className="features-title">Everything You Need to Beat the ATS</h2>
                <div className="features-grid">
                    {FEATURES.map((feature, i) => (
                        <div
                            key={i}
                            className="feature-card glass-card"
                            style={{ animationDelay: `${i * 100}ms` }}
                        >
                            <span className="feature-icon">{feature.icon}</span>
                            <h3 className="feature-name">{feature.name}</h3>
                            <p className="feature-desc">{feature.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── How It Works Section ──────────────────────────────────── */}
            <section className="how-it-works container">
                <h2 className="features-title">How It Works</h2>
                <div className="steps-grid">
                    {STEPS.map((step, i) => (
                        <div key={i} className="step-card">
                            <div className="step-number">{i + 1}</div>
                            <h3 className="step-name">{step.name}</h3>
                            <p className="step-desc">{step.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ── CTA Section ───────────────────────────────────────────── */}
            <section className="cta container">
                <div className="cta-card glass-card">
                    <h2 className="cta-title">Ready to Optimize Your Resume?</h2>
                    <p className="cta-subtitle">
                        Join thousands of job seekers who've improved their chances with ATS-optimized resumes.
                    </p>
                    <Link to="/checker" className="btn btn-primary btn-lg">
                        Get Started — It's Free
                    </Link>
                </div>
            </section>
        </div>
    );
}


// ── Feature & Step Data ──────────────────────────────────────────────────────

const FEATURES = [
    {
        icon: '🔍',
        name: 'ATS Score Checker',
        description: 'Upload your resume and get a detailed 7-dimension ATS compatibility score against any job description.',
    },
    {
        icon: '📊',
        name: 'Visual Score Report',
        description: 'Interactive radar chart, progress bars, and keyword analysis showing exactly where to improve.',
    },
    {
        icon: '💡',
        name: 'Smart Suggestions',
        description: 'AI-powered improvement suggestions with specific wording changes and missing keywords.',
    },
    {
        icon: '🔑',
        name: 'Keyword Analysis',
        description: 'See which JD keywords you hit and which you missed — the #1 factor in ATS filtering.',
    },
    {
        icon: '✨',
        name: 'Resume Generator',
        description: 'Generate a complete, ATS-optimized resume tailored to any job description using AI.',
    },
    {
        icon: '📄',
        name: 'LaTeX PDF Output',
        description: 'Professional LaTeX-typeset resumes with perfect formatting. Download PDF and .tex source.',
    },
];

const STEPS = [
    {
        name: 'Upload or Enter Profile',
        description: 'Upload your existing resume (PDF/DOCX) or fill in your profile for generation.',
    },
    {
        name: 'Paste the Job Description',
        description: 'Copy-paste the job posting you\'re applying for. Our AI analyzes it instantly.',
    },
    {
        name: 'Get Score & Suggestions',
        description: 'Receive a detailed ATS score with specific, actionable improvements to make.',
    },
    {
        name: 'Generate Optimized Resume',
        description: 'Get a beautiful, ATS-optimized LaTeX resume tailored to the exact job.',
    },
];
