"""
File Handling Utilities
=======================
Helper functions for saving uploaded files, creating download responses,
and managing temporary files during LaTeX compilation.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile
from fastapi.responses import FileResponse

from config import UPLOAD_DIR, GENERATED_DIR


# ── Allowed File Types ──────────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


async def save_upload(file: UploadFile) -> Path:
    """
    Save an uploaded resume file to the uploads directory.

    Generates a unique filename to prevent collisions, preserving the
    original file extension.

    Args:
        file: The uploaded file from the FastAPI request.

    Returns:
        Path to the saved file on disk.

    Raises:
        ValueError: If the file type is not supported (only .pdf, .docx allowed).
    """
    # Validate file extension
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{extension}'. "
            f"Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename: uuid4 + original extension
    unique_name = f"{uuid.uuid4().hex}{extension}"
    save_path = UPLOAD_DIR / unique_name

    # Write file contents to disk
    content = await file.read()
    save_path.write_bytes(content)

    return save_path


def create_download_response(
    file_path: Path,
    filename: str | None = None,
    media_type: str = "application/pdf",
) -> FileResponse:
    """
    Create a FastAPI FileResponse for downloading a generated file.

    Args:
        file_path:  Path to the file to download.
        filename:   Name to use in the Content-Disposition header.
                    Defaults to the file's actual name.
        media_type: MIME type for the response (default: application/pdf).

    Returns:
        FileResponse configured for file download.
    """
    download_name = filename or file_path.name
    return FileResponse(
        path=str(file_path),
        filename=download_name,
        media_type=media_type,
    )


def cleanup_latex_artifacts(directory: Path) -> None:
    """
    Remove intermediate LaTeX compilation artifacts from a directory.

    LaTeX generates many auxiliary files (.aux, .log, .out, etc.) during
    compilation. This function removes them, keeping only the .tex and .pdf.

    Args:
        directory: Path to the directory containing LaTeX output.
    """
    latex_junk_extensions = {".aux", ".log", ".out", ".fls", ".fdb_latexmk", ".synctex.gz"}
    for file in directory.iterdir():
        if file.suffix in latex_junk_extensions:
            file.unlink(missing_ok=True)
