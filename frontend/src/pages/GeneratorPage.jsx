/**
 * GeneratorPage — AI Resume Generator
 * ====================================
 * Allows users to generate a tailored, ATS-optimized LaTeX resume by:
 *   1. Filling in their profile (experience, education, skills, etc.)
 *   2. Pasting the target job description
 *   3. Selecting a LaTeX template
 *   4. Clicking "Generate" to get a PDF + .tex download
 */

import { useState, useEffect } from 'react';
import './GeneratorPage.css';

export default function GeneratorPage() {
    // ── State ──────────────────────────────────────────────────────
    const [templates, setTemplates] = useState([]);
    const [selectedTemplate, setSelectedTemplate] = useState('jake_resume');
    const [jobDescription, setJobDescription] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    // Profile state
    const [profile, setProfile] = useState({
        name: '',
        email: '',
        phone: '',
        linkedin: '',
        github: '',
        location: '',
        experience: [{ title: '', company: '', start_date: '', end_date: '', description: '' }],
        education: [{ degree: '', institution: '', graduation_date: '' }],
        skills: '',
        projects: [{ name: '', description: '' }],
        certifications: '',
    });

    // ── Load templates on mount ────────────────────────────────────
    useEffect(() => {
        fetch('/api/templates')
            .then(res => res.json())
            .then(data => setTemplates(data.templates || []))
            .catch(() => { });
    }, []);

    // ── Profile Update Helpers ─────────────────────────────────────

    const updateProfile = (field, value) => {
        setProfile(prev => ({ ...prev, [field]: value }));
    };

    const updateExperience = (index, field, value) => {
        setProfile(prev => {
            const newExp = [...prev.experience];
            newExp[index] = { ...newExp[index], [field]: value };
            return { ...prev, experience: newExp };
        });
    };

    const addExperience = () => {
        setProfile(prev => ({
            ...prev,
            experience: [...prev.experience, { title: '', company: '', start_date: '', end_date: '', description: '' }],
        }));
    };

    const updateEducation = (index, field, value) => {
        setProfile(prev => {
            const newEdu = [...prev.education];
            newEdu[index] = { ...newEdu[index], [field]: value };
            return { ...prev, education: newEdu };
        });
    };

    const addEducation = () => {
        setProfile(prev => ({
            ...prev,
            education: [...prev.education, { degree: '', institution: '', graduation_date: '' }],
        }));
    };

    const updateProject = (index, field, value) => {
        setProfile(prev => {
            const newProj = [...prev.projects];
            newProj[index] = { ...newProj[index], [field]: value };
            return { ...prev, projects: newProj };
        });
    };

    const addProject = () => {
        setProfile(prev => ({
            ...prev,
            projects: [...prev.projects, { name: '', description: '' }],
        }));
    };

    // ── Generate Resume ────────────────────────────────────────────

    const handleGenerate = async () => {
        if (!profile.name.trim()) {
            setError('Please enter your name.');
            return;
        }
        if (!jobDescription.trim()) {
            setError('Please paste the job description.');
            return;
        }

        setLoading(true);
        setError('');
        setResult(null);

        try {
            // Prepare profile data
            const profileData = {
                ...profile,
                skills: profile.skills.split(',').map(s => s.trim()).filter(Boolean),
                certifications: profile.certifications.split(',').map(s => s.trim()).filter(Boolean),
            };

            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    profile: profileData,
                    job_description_text: jobDescription,
                    template_id: selectedTemplate,
                }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Generation failed');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err.message || 'Failed to generate resume.');
        } finally {
            setLoading(false);
        }
    };

    // ── Render ─────────────────────────────────────────────────────

    return (
        <div className="generator-page container">
            <div className="page-header animate-fade-in">
                <h1 className="page-title">✨ AI Resume Generator</h1>
                <p className="page-subtitle">
                    Fill in your profile, paste the job description, and get a tailored
                    LaTeX resume optimized for ATS systems.
                </p>
            </div>

            <div className="generator-grid">
                {/* ── Left: Profile Form ─────────────────────────────────── */}
                <div className="form-column">
                    {/* Basic Info */}
                    <div className="form-section glass-card">
                        <h2 className="form-section-title">👤 Basic Information</h2>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Full Name *</label>
                                <input className="form-input" placeholder="John Doe" value={profile.name} onChange={e => updateProfile('name', e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Email</label>
                                <input className="form-input" placeholder="john@example.com" value={profile.email} onChange={e => updateProfile('email', e.target.value)} />
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Phone</label>
                                <input className="form-input" placeholder="+1 234 567 8900" value={profile.phone} onChange={e => updateProfile('phone', e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Location</label>
                                <input className="form-input" placeholder="San Francisco, CA" value={profile.location} onChange={e => updateProfile('location', e.target.value)} />
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">LinkedIn</label>
                                <input className="form-input" placeholder="linkedin.com/in/johndoe" value={profile.linkedin} onChange={e => updateProfile('linkedin', e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">GitHub</label>
                                <input className="form-input" placeholder="github.com/johndoe" value={profile.github} onChange={e => updateProfile('github', e.target.value)} />
                            </div>
                        </div>
                    </div>

                    {/* Experience */}
                    <div className="form-section glass-card">
                        <h2 className="form-section-title">💼 Work Experience</h2>
                        {profile.experience.map((exp, i) => (
                            <div key={i} className="repeatable-item">
                                {i > 0 && <hr className="item-divider" />}
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Job Title</label>
                                        <input className="form-input" placeholder="Software Engineer" value={exp.title} onChange={e => updateExperience(i, 'title', e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Company</label>
                                        <input className="form-input" placeholder="Google" value={exp.company} onChange={e => updateExperience(i, 'company', e.target.value)} />
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Start Date</label>
                                        <input className="form-input" placeholder="Jan 2022" value={exp.start_date} onChange={e => updateExperience(i, 'start_date', e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">End Date</label>
                                        <input className="form-input" placeholder="Present" value={exp.end_date} onChange={e => updateExperience(i, 'end_date', e.target.value)} />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Description / Key Achievements</label>
                                    <textarea className="form-textarea" placeholder="Led a team of 5 engineers to build..." rows={3} value={exp.description} onChange={e => updateExperience(i, 'description', e.target.value)} />
                                </div>
                            </div>
                        ))}
                        <button className="btn btn-secondary add-btn" onClick={addExperience}>+ Add Experience</button>
                    </div>

                    {/* Education */}
                    <div className="form-section glass-card">
                        <h2 className="form-section-title">🎓 Education</h2>
                        {profile.education.map((edu, i) => (
                            <div key={i} className="repeatable-item">
                                {i > 0 && <hr className="item-divider" />}
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Degree</label>
                                        <input className="form-input" placeholder="B.S. in Computer Science" value={edu.degree} onChange={e => updateEducation(i, 'degree', e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Institution</label>
                                        <input className="form-input" placeholder="Stanford University" value={edu.institution} onChange={e => updateEducation(i, 'institution', e.target.value)} />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Graduation Date</label>
                                    <input className="form-input" placeholder="May 2021" value={edu.graduation_date} onChange={e => updateEducation(i, 'graduation_date', e.target.value)} />
                                </div>
                            </div>
                        ))}
                        <button className="btn btn-secondary add-btn" onClick={addEducation}>+ Add Education</button>
                    </div>

                    {/* Skills */}
                    <div className="form-section glass-card">
                        <h2 className="form-section-title">🛠️ Skills</h2>
                        <div className="form-group">
                            <label className="form-label">Skills (comma-separated)</label>
                            <textarea className="form-textarea" placeholder="Python, JavaScript, React, Node.js, PostgreSQL, Docker, AWS..." rows={3} value={profile.skills} onChange={e => updateProfile('skills', e.target.value)} />
                        </div>
                    </div>

                    {/* Projects */}
                    <div className="form-section glass-card">
                        <h2 className="form-section-title">🚀 Projects</h2>
                        {profile.projects.map((proj, i) => (
                            <div key={i} className="repeatable-item">
                                {i > 0 && <hr className="item-divider" />}
                                <div className="form-group">
                                    <label className="form-label">Project Name</label>
                                    <input className="form-input" placeholder="E-commerce Platform" value={proj.name} onChange={e => updateProject(i, 'name', e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Description</label>
                                    <textarea className="form-textarea" placeholder="Built a full-stack e-commerce platform using React and Node.js..." rows={2} value={proj.description} onChange={e => updateProject(i, 'description', e.target.value)} />
                                </div>
                            </div>
                        ))}
                        <button className="btn btn-secondary add-btn" onClick={addProject}>+ Add Project</button>
                    </div>

                    {/* Certifications */}
                    <div className="form-section glass-card">
                        <h2 className="form-section-title">📜 Certifications</h2>
                        <div className="form-group">
                            <label className="form-label">Certifications (comma-separated)</label>
                            <input className="form-input" placeholder="AWS Solutions Architect, Google Cloud Professional..." value={profile.certifications} onChange={e => updateProfile('certifications', e.target.value)} />
                        </div>
                    </div>
                </div>

                {/* ── Right: JD + Template + Generate ─────────────────────── */}
                <div className="config-column">
                    {/* Job Description */}
                    <div className="form-section glass-card">
                        <h2 className="form-section-title">💼 Target Job Description *</h2>
                        <textarea
                            className="form-textarea"
                            placeholder="Paste the job description you're applying for..."
                            rows={10}
                            value={jobDescription}
                            onChange={e => setJobDescription(e.target.value)}
                        />
                    </div>

                    {/* Template Selection */}
                    <div className="form-section glass-card">
                        <h2 className="form-section-title">📐 Resume Template</h2>
                        <div className="template-grid">
                            {(templates.length > 0 ? templates : [
                                { id: 'jake_resume', name: "Jake's Resume", description: 'Clean, ATS-optimized. Popular in tech.' },
                                { id: 'modern_professional', name: 'Modern Professional', description: 'Elegant, suitable for all industries.' },
                            ]).map(t => (
                                <div
                                    key={t.id}
                                    className={`template-card ${selectedTemplate === t.id ? 'selected' : ''}`}
                                    onClick={() => setSelectedTemplate(t.id)}
                                >
                                    <div className="template-preview">📄</div>
                                    <h4 className="template-name">{t.name}</h4>
                                    <p className="template-desc">{t.description}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Generate Button */}
                    <button
                        className="btn btn-success btn-lg generate-btn"
                        onClick={handleGenerate}
                        disabled={loading || !profile.name.trim() || !jobDescription.trim()}
                    >
                        {loading ? (
                            <>
                                <span className="spinner"></span>
                                Generating with AI...
                            </>
                        ) : (
                            '✨ Generate Resume'
                        )}
                    </button>

                    {error && <p className="generator-error">{error}</p>}

                    {/* Result */}
                    {result && (
                        <div className="generation-result glass-card animate-slide-up">
                            <h3 className="result-title">
                                {result.success ? '🎉 Resume Generated!' : '⚠️ Partial Success'}
                            </h3>
                            <p className="result-message">{result.message}</p>

                            <div className="result-actions">
                                {result.pdf_available && result.download_url_pdf && (
                                    <a
                                        href={result.download_url_pdf}
                                        className="btn btn-primary"
                                        download
                                    >
                                        📥 Download PDF
                                    </a>
                                )}
                                {result.download_url_tex && (
                                    <a
                                        href={result.download_url_tex}
                                        className="btn btn-secondary"
                                        download
                                    >
                                        📄 Download .tex Source
                                    </a>
                                )}
                            </div>

                            {result.compilation_error && (
                                <div className="compilation-warning">
                                    <p className="warning-title">⚠️ LaTeX Compilation Note:</p>
                                    <p className="warning-text">{result.compilation_error}</p>
                                    <p className="warning-hint">
                                        You can compile the .tex file manually using Overleaf or
                                        any LaTeX editor on your machine.
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
