/**
 * SuggestionPanel Component
 * =========================
 * Displays prioritized improvement suggestions from the scoring
 * engine, grouped by priority (high, medium, low) with color-coded badges.
 */

import './SuggestionPanel.css';

export default function SuggestionPanel({ suggestions }) {
    if (!suggestions || suggestions.length === 0) return null;

    // Group by priority
    const high = suggestions.filter(s => s.priority === 'high');
    const medium = suggestions.filter(s => s.priority === 'medium');
    const low = suggestions.filter(s => s.priority === 'low');

    return (
        <div className="suggestion-panel score-section">
            <h3 className="section-title">💡 Improvement Suggestions</h3>

            {high.length > 0 && (
                <div className="suggestion-group">
                    <h4 className="suggestion-group-title">
                        <span className="badge badge-high">High Priority</span>
                    </h4>
                    {high.map((s, i) => (
                        <SuggestionCard key={`h${i}`} suggestion={s} />
                    ))}
                </div>
            )}

            {medium.length > 0 && (
                <div className="suggestion-group">
                    <h4 className="suggestion-group-title">
                        <span className="badge badge-medium">Medium Priority</span>
                    </h4>
                    {medium.map((s, i) => (
                        <SuggestionCard key={`m${i}`} suggestion={s} />
                    ))}
                </div>
            )}

            {low.length > 0 && (
                <div className="suggestion-group">
                    <h4 className="suggestion-group-title">
                        <span className="badge badge-low">Low Priority</span>
                    </h4>
                    {low.map((s, i) => (
                        <SuggestionCard key={`l${i}`} suggestion={s} />
                    ))}
                </div>
            )}
        </div>
    );
}


function SuggestionCard({ suggestion }) {
    const categoryIcons = {
        'Keywords': '🔑',
        'Keyword Match': '🔑',
        'Skill Relevance': '🎯',
        'Content': '📝',
        'Structure': '🏗️',
        'Formatting': '📋',
        'Formatting Score': '📋',
        'Section Completeness': '📂',
        'Experience Alignment': '💼',
        'Education Match': '🎓',
        'Action Verb Usage': '💪',
        'Impact': '🚀',
    };

    const icon = categoryIcons[suggestion.category] || '💡';

    return (
        <div className="suggestion-card">
            <span className="suggestion-icon">{icon}</span>
            <div className="suggestion-content">
                <span className="suggestion-category">{suggestion.category}</span>
                <p className="suggestion-message">{suggestion.message}</p>
            </div>
        </div>
    );
}
