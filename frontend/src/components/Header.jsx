/**
 * Header Component
 * ================
 * Navigation bar with branding, page links, and a gradient accent.
 * Fixed at the top with a glass blur effect.
 */

import { NavLink } from 'react-router-dom';
import './Header.css';

export default function Header() {
    return (
        <header className="header">
            <div className="header-inner container">
                {/* Logo / Brand */}
                <NavLink to="/" className="header-brand">
                    <span className="header-logo">📄</span>
                    <span className="header-title">ATS Checker</span>
                </NavLink>

                {/* Navigation Links */}
                <nav className="header-nav">
                    <NavLink
                        to="/checker"
                        className={({ isActive }) => `header-link ${isActive ? 'active' : ''}`}
                    >
                        🔍 Score Checker
                    </NavLink>
                    <NavLink
                        to="/generator"
                        className={({ isActive }) => `header-link ${isActive ? 'active' : ''}`}
                    >
                        ✨ Resume Generator
                    </NavLink>
                </nav>
            </div>
        </header>
    );
}
