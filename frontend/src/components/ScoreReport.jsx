/**
 * ScoreReport Component
 * =====================
 * Displays the ATS score results with:
 *   - Overall score ring with gradient
 *   - Letter grade badge
 *   - 7-dimension progress bars
 *   - Keyword match/miss lists
 *   - Radar chart visualization
 */

import RadarChart from './RadarChart.jsx';
import SuggestionPanel from './SuggestionPanel.jsx';
import './ScoreReport.css';

export default function ScoreReport({ report }) {
    if (!report) return null;

    const { overall_score, grade, dimensions, summary, keywords_found, keywords_missing } = report;

    // Determine grade color
    const gradeColor = getGradeColor(grade);

    return (
        <div className="score-report animate-slide-up">
            {/* ── Overall Score Section ────────────────────────────────── */}
            <div className="score-hero">
                <div className="score-ring" style={{ '--score': overall_score }}>
                    <svg viewBox="0 0 120 120" className="score-ring-svg">
                        <circle cx="60" cy="60" r="54" className="score-ring-bg" />
                        <circle
                            cx="60" cy="60" r="54"
                            className="score-ring-fill"
                            style={{
                                strokeDasharray: `${(overall_score / 100) * 339.3} 339.3`,
                                stroke: gradeColor,
                            }}
                        />
                    </svg>
                    <div className="score-ring-content">
                        <span className="score-number">{Math.round(overall_score)}</span>
                        <span className="score-label">/ 100</span>
                    </div>
                </div>

                <div className="score-info">
                    <div className="grade-badge" style={{ backgroundColor: gradeColor + '22', color: gradeColor, borderColor: gradeColor + '44' }}>
                        Grade: {grade}
                    </div>
                    <p className="score-summary">{summary}</p>
                </div>
            </div>

            {/* ── Radar Chart ─────────────────────────────────────────── */}
            <div className="score-section">
                <h3 className="section-title">Score Breakdown</h3>
                <div className="score-chart-container">
                    <RadarChart dimensions={dimensions} />
                </div>
            </div>

            {/* ── Dimension Progress Bars ─────────────────────────────── */}
            <div className="score-section">
                <h3 className="section-title">Dimension Scores</h3>
                <div className="dimensions-list">
                    {dimensions.map((dim) => (
                        <div key={dim.name} className="dimension-item">
                            <div className="dimension-header">
                                <span className="dimension-name">{dim.name}</span>
                                <span className="dimension-value">{Math.round(dim.score)}/100</span>
                            </div>
                            <div className="dimension-bar">
                                <div
                                    className="dimension-bar-fill"
                                    style={{
                                        width: `${dim.score}%`,
                                        background: getScoreGradient(dim.score),
                                    }}
                                />
                            </div>
                            <p className="dimension-details">{dim.details}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* ── Keywords Section ─────────────────────────────────────── */}
            <div className="score-section">
                <h3 className="section-title">Keyword Analysis</h3>
                <div className="keywords-grid">
                    <div className="keywords-group">
                        <h4 className="keywords-label found">✅ Found ({keywords_found.length})</h4>
                        <div className="keywords-list">
                            {keywords_found.map((kw, i) => (
                                <span key={i} className="keyword-tag found">{kw}</span>
                            ))}
                            {keywords_found.length === 0 && (
                                <span className="text-muted">No matching keywords found</span>
                            )}
                        </div>
                    </div>
                    <div className="keywords-group">
                        <h4 className="keywords-label missing">❌ Missing ({keywords_missing.length})</h4>
                        <div className="keywords-list">
                            {keywords_missing.map((kw, i) => (
                                <span key={i} className="keyword-tag missing">{kw}</span>
                            ))}
                            {keywords_missing.length === 0 && (
                                <span className="text-muted">All keywords matched!</span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Suggestions ──────────────────────────────────────────── */}
            <SuggestionPanel suggestions={report.suggestions} />
        </div>
    );
}


// ── Helper Functions ─────────────────────────────────────────────────────────

function getGradeColor(grade) {
    const colors = {
        'A+': '#10b981', 'A': '#10b981',
        'B+': '#3b82f6', 'B': '#3b82f6',
        'C+': '#f59e0b', 'C': '#f59e0b',
        'D': '#ef4444', 'F': '#ef4444',
    };
    return colors[grade] || '#3b82f6';
}

function getScoreGradient(score) {
    if (score >= 80) return 'linear-gradient(90deg, #10b981, #34d399)';
    if (score >= 60) return 'linear-gradient(90deg, #3b82f6, #60a5fa)';
    if (score >= 40) return 'linear-gradient(90deg, #f59e0b, #fbbf24)';
    return 'linear-gradient(90deg, #ef4444, #f87171)';
}
