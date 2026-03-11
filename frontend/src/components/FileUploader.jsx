/**
 * FileUploader Component
 * ======================
 * Drag-and-drop file upload zone for resume files (PDF/DOCX).
 * Shows file info after selection and validates file type.
 */

import { useState, useRef } from 'react';
import './FileUploader.css';

export default function FileUploader({ onFileSelect, onTextExtracted }) {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');
    const inputRef = useRef(null);

    const allowedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ];

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(e.type === 'dragenter' || e.type === 'dragover');
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        const file = e.dataTransfer.files[0];
        if (file) processFile(file);
    };

    const handleChange = (e) => {
        const file = e.target.files[0];
        if (file) processFile(file);
    };

    const processFile = async (file) => {
        setError('');

        // Validate file type
        if (!allowedTypes.includes(file.type)) {
            setError('Please upload a PDF or DOCX file.');
            return;
        }

        // Validate file size (10MB max)
        if (file.size > 10 * 1024 * 1024) {
            setError('File size must be less than 10MB.');
            return;
        }

        setSelectedFile(file);
        if (onFileSelect) onFileSelect(file);

        // Upload and parse the file
        await uploadAndParse(file);
    };

    const uploadAndParse = async (file) => {
        setUploading(true);
        setError('');

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/resume/parse', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.success && data.resume_data) {
                onTextExtracted(data.resume_data);
            } else {
                setError(data.detail || data.message || 'Failed to parse resume.');
            }
        } catch (err) {
            setError('Upload failed. Make sure the backend is running.');
        } finally {
            setUploading(false);
        }
    };

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
        <div className="file-uploader">
            {/* Drop Zone */}
            <div
                className={`drop-zone ${dragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
            >
                <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleChange}
                    className="drop-zone-input"
                />

                {uploading ? (
                    <div className="drop-zone-uploading">
                        <div className="spinner"></div>
                        <p>Parsing resume...</p>
                    </div>
                ) : selectedFile ? (
                    <div className="drop-zone-file">
                        <span className="file-icon">
                            {selectedFile.name.endsWith('.pdf') ? '📕' : '📘'}
                        </span>
                        <div className="file-info">
                            <span className="file-name">{selectedFile.name}</span>
                            <span className="file-size">{formatFileSize(selectedFile.size)}</span>
                        </div>
                        <span className="file-status">✅ Parsed</span>
                    </div>
                ) : (
                    <div className="drop-zone-prompt">
                        <span className="drop-zone-icon">📄</span>
                        <p className="drop-zone-text">
                            <strong>Drop your resume here</strong> or click to browse
                        </p>
                        <p className="drop-zone-hint">PDF or DOCX • Max 10MB</p>
                    </div>
                )}
            </div>

            {/* Error Message */}
            {error && <p className="upload-error">{error}</p>}
        </div>
    );
}
