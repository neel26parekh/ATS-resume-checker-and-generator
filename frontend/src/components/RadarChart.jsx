/**
 * RadarChart Component
 * ====================
 * Custom canvas-based 7-axis radar chart for visualizing
 * ATS score dimensions. No external charting library needed.
 */

import { useRef, useEffect } from 'react';
import './RadarChart.css';

const CHART_SIZE = 300;
const CENTER = CHART_SIZE / 2;
const RADIUS = 120;

export default function RadarChart({ dimensions }) {
    const canvasRef = useRef(null);

    useEffect(() => {
        if (!dimensions || dimensions.length === 0) return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;

        // Set canvas resolution for retina displays
        canvas.width = CHART_SIZE * dpr;
        canvas.height = CHART_SIZE * dpr;
        ctx.scale(dpr, dpr);

        drawChart(ctx, dimensions);
    }, [dimensions]);

    return (
        <div className="radar-chart">
            <canvas
                ref={canvasRef}
                style={{ width: CHART_SIZE, height: CHART_SIZE }}
            />
        </div>
    );
}


/**
 * Draw the complete radar chart: grid, data polygon, labels.
 */
function drawChart(ctx, dimensions) {
    const n = dimensions.length;
    const angleStep = (2 * Math.PI) / n;

    // Clear canvas
    ctx.clearRect(0, 0, CHART_SIZE, CHART_SIZE);

    // ── Draw grid rings ────────────────────────────────────────────────────
    const gridLevels = [0.25, 0.5, 0.75, 1.0];
    for (const level of gridLevels) {
        ctx.beginPath();
        for (let i = 0; i <= n; i++) {
            const angle = i * angleStep - Math.PI / 2;
            const x = CENTER + RADIUS * level * Math.cos(angle);
            const y = CENTER + RADIUS * level * Math.sin(angle);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    // ── Draw axis lines ────────────────────────────────────────────────────
    for (let i = 0; i < n; i++) {
        const angle = i * angleStep - Math.PI / 2;
        ctx.beginPath();
        ctx.moveTo(CENTER, CENTER);
        ctx.lineTo(
            CENTER + RADIUS * Math.cos(angle),
            CENTER + RADIUS * Math.sin(angle),
        );
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
        ctx.lineWidth = 1;
        ctx.stroke();
    }

    // ── Draw data polygon (filled) ─────────────────────────────────────────
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
        const idx = i % n;
        const angle = idx * angleStep - Math.PI / 2;
        const value = dimensions[idx].score / 100;
        const x = CENTER + RADIUS * value * Math.cos(angle);
        const y = CENTER + RADIUS * value * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.fillStyle = 'rgba(59, 130, 246, 0.15)';
    ctx.fill();
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.stroke();

    // ── Draw data points ───────────────────────────────────────────────────
    for (let i = 0; i < n; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const value = dimensions[i].score / 100;
        const x = CENTER + RADIUS * value * Math.cos(angle);
        const y = CENTER + RADIUS * value * Math.sin(angle);

        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fillStyle = '#60a5fa';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }

    // ── Draw labels ────────────────────────────────────────────────────────
    ctx.font = '11px Inter, sans-serif';
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let i = 0; i < n; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const labelRadius = RADIUS + 25;
        const x = CENTER + labelRadius * Math.cos(angle);
        const y = CENTER + labelRadius * Math.sin(angle);

        // Shorten long labels
        const shortName = shortenLabel(dimensions[i].name);
        ctx.fillText(shortName, x, y);
    }
}


/** Shorten dimension labels for the chart. */
function shortenLabel(name) {
    const map = {
        'Keyword Match': 'Keywords',
        'Skill Relevance': 'Skills',
        'Experience Alignment': 'Experience',
        'Education Match': 'Education',
        'Formatting Score': 'Formatting',
        'Section Completeness': 'Sections',
        'Action Verb Usage': 'Verbs',
    };
    return map[name] || name;
}
