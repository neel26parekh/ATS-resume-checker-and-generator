/**
 * CheckerPage — ATS Score Checker
 * ================================
 * The main feature page where users:
 *   1. Upload their resume (or paste text)
 *   2. Paste the job description
 *   3. Click "Check Score" to get the ATS report
 *
 * Results include the full ScoreReport with radar chart,
 * dimension breakdown, keyword analysis, and suggestions.
 */

import { useState } from 'react';
import FileUploader from '../components/FileUploader.jsx';
import ScoreReport from '../components/ScoreReport.jsx';
import './CheckerPage.css';

export default function CheckerPage() {
    // ── State ──────────────────────────────────────────────────────
    const [resumeText, setResumeText] = useState('');
    const [jobDescription, setJobDescription] = useState('');
    const [resumeData, setResumeData] = useState(null);
    const [scoreReport, setScoreReport] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [inputMode, setInputMode] = useState('upload'); // 'upload' | 'paste'

    // ── Handlers ───────────────────────────────────────────────────

    const handleTextExtracted = (data) => {
        setResumeData(data);
        setResumeText(data.raw_text);
        setError('');
    };

    const handleCheckScore = async () => {
        if (!resumeText.trim()) {
            setError('Please upload a resume or paste your resume text.');
            return;
        }
        if (!jobDescription.trim()) {
            setError('Please paste the job description.');
            return;
        }

        setLoading(true);
        setError('');
        setScoreReport(null);

        try {
            const response = await fetch('/api/score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    resume_text: resumeText,
                    job_description_text: jobDescription,
                }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Scoring failed');
            }

            const report = await response.json();
            setScoreReport(report);
        } catch (err) {
            setError(err.message || 'Failed to score resume. Is the backend running?');
        } finally {
            setLoading(false);
        }
    };

    // ── Render ─────────────────────────────────────────────────────

    return (
        <div className="checker-page container">
            <div className="page-header animate-fade-in">
                <h1 className="page-title">🔍 ATS Score Checker</h1>
                <p className="page-subtitle">
                    Upload your resume and paste a job description to get a detailed
                    ATS compatibility analysis with actionable improvement suggestions.
                </p>
            </div>

            <div className="checker-grid">
                {/* ── Left Column: Inputs ───────────────────────────────── */}
                <div className="input-column">
                    {/* Resume Input */}
                    <div className="input-section glass-card">
                        <h2 className="input-title">📄 Your Resume</h2>

                        {/* Input Mode Toggle */}
                        <div className="input-toggle">
                            <button
                                className={`toggle-btn ${inputMode === 'upload' ? 'active' : ''}`}
                                onClick={() => setInputMode('upload')}
                            >
                                Upload File
                            </button>
                            <button
                                className={`toggle-btn ${inputMode === 'paste' ? 'active' : ''}`}
                                onClick={() => setInputMode('paste')}
                            >
                                Paste Text
                            </button>
                        </div>

                        {inputMode === 'upload' ? (
                            <FileUploader
                                onFileSelect={() => { }}
                                onTextExtracted={handleTextExtracted}
                            />
                        ) : (
                            <textarea
                                className="form-textarea resume-textarea"
                                placeholder="Paste your full resume text here..."
                                value={resumeText}
                                onChange={(e) => setResumeText(e.target.value)}
                                rows={12}
                            />
                        )}

                        {resumeData && inputMode === 'upload' && (
                            <div className="parse-info">
                                <span className="parse-badge">
                                    ✅ {resumeData.sections?.length || 0} sections detected
                                </span>
                                <span className="parse-badge">
                                    🔑 {resumeData.detected_skills?.length || 0} skills found
                                </span>
                                {resumeData.formatting_issues?.length > 0 && (
                                    <span className="parse-badge warning">
                                        ⚠️ {resumeData.formatting_issues.length} formatting issues
                                    </span>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Job Description Input */}
                    <div className="input-section glass-card">
                        <h2 className="input-title">💼 Job Description</h2>
                        <textarea
                            className="form-textarea jd-textarea"
                            placeholder="Paste the job description here... (copy from LinkedIn, Indeed, etc.)"
                            value={jobDescription}
                            onChange={(e) => setJobDescription(e.target.value)}
                            rows={10}
                        />
                    </div>

                    {/* Action Button */}
                    <button
                        className="btn btn-primary btn-lg check-btn"
                        onClick={handleCheckScore}
                        disabled={loading || !resumeText.trim() || !jobDescription.trim()}
                    >
                        {loading ? (
                            <>
                                <span className="spinner"></span>
                                Analyzing with AI...
                            </>
                        ) : (
                            '🚀 Check ATS Score'
                        )}
                    </button>

                    {error && <p className="checker-error">{error}</p>}
                </div>

                {/* ── Right Column: Results ─────────────────────────────── */}
                <div className="results-column">
                    {loading && (
                        <div className="loading-overlay glass-card">
                            <div className="spinner spinner-lg"></div>
                            <h3>Analyzing Your Resume</h3>
                            <p className="text-muted">
                                Running 7-dimension ATS analysis with AI...
                            </p>
                        </div>
                    )}

                    {scoreReport && <ScoreReport report={scoreReport} />}

                    {!scoreReport && !loading && (
                        <div className="results-placeholder glass-card">
                            <span className="placeholder-icon">📊</span>
                            <h3>Your Score Report Will Appear Here</h3>
                            <p className="text-muted">
                                Upload your resume and paste a job description,
                                then click "Check ATS Score" to get started.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
