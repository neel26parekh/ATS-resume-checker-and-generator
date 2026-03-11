"""
LaTeX Compiler Service
======================
Renders Jinja2 LaTeX templates with resume data and compiles them
to PDF using pdflatex or tectonic.

Pipeline:
    1. Load a LaTeX Jinja2 template (.tex.j2)
    2. Fill template variables with resume data
    3. Write the rendered .tex file to disk
    4. Compile using pdflatex/tectonic → produce .pdf
    5. Return paths to both .tex and .pdf files

Usage:
    from services.latex_compiler import render_and_compile

    result = await render_and_compile(resume_data, "jake_resume")
    print(result["pdf_path"])
    print(result["tex_path"])
"""

import shutil
import subprocess
import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config import TEMPLATES_DIR, GENERATED_DIR


# ── Jinja2 LaTeX Environment ───────────────────────────────────────────────
# Custom delimiters to avoid conflicts with LaTeX's use of { and }
# We use <<= >> for variables, <<* *>> for blocks, <<# #>> for comments

_latex_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    block_start_string="<<*",
    block_end_string="*>>",
    variable_start_string="<<=",
    variable_end_string="=>>",
    comment_start_string="<<#",
    comment_end_string="#>>",
    autoescape=False,  # LaTeX is not HTML — no auto-escaping
)


# ── Available Templates ─────────────────────────────────────────────────────

AVAILABLE_TEMPLATES = {
    "jake_resume": {
        "file": "jake_resume.tex.j2",
        "name": "Jake's Resume",
        "description": "Clean, single-column, ATS-optimized template. Popular in tech.",
    },
    "modern_professional": {
        "file": "modern_professional.tex.j2",
        "name": "Modern Professional",
        "description": "Elegant, professional template suitable for all industries.",
    },
}


def get_available_templates() -> list[dict]:
    """
    Return the list of available LaTeX templates.

    Returns:
        List of template info dictionaries with 'id', 'name', 'description'.
    """
    return [
        {"id": tid, "name": t["name"], "description": t["description"]}
        for tid, t in AVAILABLE_TEMPLATES.items()
    ]


# ── Public API ──────────────────────────────────────────────────────────────

async def render_and_compile(
    resume_data: dict,
    template_id: str = "jake_resume",
) -> dict:
    """
    Render a LaTeX template with resume data and compile to PDF.

    Args:
        resume_data:  Dictionary with resume content (from resume_generator).
        template_id:  ID of the template to use (default: "jake_resume").

    Returns:
        Dictionary with:
            - 'pdf_path': Path to the generated PDF file.
            - 'tex_path': Path to the rendered .tex source file.
            - 'success': Whether compilation succeeded.
            - 'error': Error message (if compilation failed).

    Raises:
        ValueError: If the template_id is not recognized.
    """
    if template_id not in AVAILABLE_TEMPLATES:
        raise ValueError(
            f"Unknown template '{template_id}'. "
            f"Available: {', '.join(AVAILABLE_TEMPLATES.keys())}"
        )

    template_info = AVAILABLE_TEMPLATES[template_id]

    # Create a unique output directory for this generation
    job_id = uuid.uuid4().hex[:12]
    output_dir = GENERATED_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Render the LaTeX template
    tex_content = _render_template(template_info["file"], resume_data)

    # Step 2: Write the .tex file
    tex_path = output_dir / "resume.tex"
    tex_path.write_text(tex_content, encoding="utf-8")

    # Step 3: Compile to PDF
    success, error = _compile_latex(tex_path, output_dir)

    pdf_path = output_dir / "resume.pdf"

    return {
        "pdf_path": str(pdf_path) if pdf_path.exists() else None,
        "tex_path": str(tex_path),
        "success": success,
        "error": error,
        "job_id": job_id,
    }


# ── Template Rendering ──────────────────────────────────────────────────────

def _render_template(template_file: str, resume_data: dict) -> str:
    """
    Render a Jinja2 LaTeX template with resume data.

    Escapes special LaTeX characters in the data before rendering.

    Args:
        template_file: Filename of the .tex.j2 template.
        resume_data:   Dictionary with resume content.

    Returns:
        Rendered LaTeX source code as a string.
    """
    template = _latex_env.get_template(template_file)

    # Deep-escape all string values for LaTeX
    escaped_data = _escape_latex_recursive(resume_data)

    return template.render(**escaped_data)


def _escape_latex(text: str) -> str:
    """
    Escape special LaTeX characters in a string.

    Characters that have special meaning in LaTeX:
        & % $ # _ { } ~ ^ \\

    Args:
        text: Raw text string.

    Returns:
        LaTeX-safe string with special characters escaped.
    """
    if not isinstance(text, str):
        return text

    # Order matters — backslash must be first
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]

    for char, replacement in replacements:
        text = text.replace(char, replacement)

    return text


def _escape_latex_recursive(data):
    """
    Recursively escape all string values in a nested data structure.

    Handles dicts, lists, and strings.

    Args:
        data: Data structure to escape (dict, list, or str).

    Returns:
        New data structure with all strings escaped.
    """
    if isinstance(data, str):
        return _escape_latex(data)
    elif isinstance(data, dict):
        return {k: _escape_latex_recursive(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_escape_latex_recursive(item) for item in data]
    else:
        return data


# ── LaTeX Compilation ───────────────────────────────────────────────────────

def _compile_latex(tex_path: Path, output_dir: Path) -> tuple[bool, str | None]:
    """
    Compile a .tex file to PDF using pdflatex or tectonic.

    Tries pdflatex first, then tectonic as a fallback.

    Args:
        tex_path:   Path to the .tex file to compile.
        output_dir: Directory for output files.

    Returns:
        Tuple of (success: bool, error_message: str | None).
    """
    # Try pdflatex first (most common)
    if shutil.which("pdflatex"):
        return _compile_with_pdflatex(tex_path, output_dir)

    # Try tectonic as fallback (simpler, auto-downloads packages)
    if shutil.which("tectonic"):
        return _compile_with_tectonic(tex_path)

    # Neither compiler available
    return False, (
        "No LaTeX compiler found. Please install either:\n"
        "  - pdflatex (via MacTeX/MiKTeX/TeX Live)\n"
        "  - tectonic (cargo install tectonic, or brew install tectonic)\n"
        "The .tex source file has been generated — you can compile it manually."
    )


def _compile_with_pdflatex(tex_path: Path, output_dir: Path) -> tuple[bool, str | None]:
    """Compile using pdflatex (run twice for cross-references)."""
    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={output_dir}",
        str(tex_path),
    ]

    try:
        # Run twice to resolve references
        for _ in range(2):
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(output_dir),
            )

        if result.returncode == 0:
            _cleanup_latex_junk(output_dir)
            return True, None
        else:
            # Extract meaningful error from log
            error = _extract_latex_error(result.stdout + result.stderr)
            return False, error

    except subprocess.TimeoutExpired:
        return False, "LaTeX compilation timed out (30s limit)."
    except FileNotFoundError:
        return False, "pdflatex command not found."


def _compile_with_tectonic(tex_path: Path) -> tuple[bool, str | None]:
    """Compile using tectonic (auto-downloads packages)."""
    try:
        result = subprocess.run(
            ["tectonic", str(tex_path)],
            capture_output=True,
            text=True,
            timeout=60,  # tectonic may need to download packages
        )

        if result.returncode == 0:
            return True, None
        else:
            return False, f"Tectonic error: {result.stderr[:500]}"

    except subprocess.TimeoutExpired:
        return False, "Tectonic compilation timed out (60s limit)."
    except FileNotFoundError:
        return False, "tectonic command not found."


# ── Cleanup ─────────────────────────────────────────────────────────────────

def _cleanup_latex_junk(directory: Path) -> None:
    """Remove intermediate LaTeX files, keeping only .tex and .pdf."""
    junk_extensions = {".aux", ".log", ".out", ".fls", ".fdb_latexmk", ".synctex.gz"}
    for file in directory.iterdir():
        if file.suffix in junk_extensions:
            file.unlink(missing_ok=True)


def _extract_latex_error(log_text: str) -> str:
    """Extract meaningful error messages from LaTeX log output."""
    # Look for lines starting with "!" (LaTeX error indicator)
    error_lines = [
        line.strip() for line in log_text.split("\n")
        if line.strip().startswith("!")
    ]

    if error_lines:
        return "; ".join(error_lines[:3])

    # Fallback: return last 200 characters of log
    return f"LaTeX compilation failed. Log excerpt: {log_text[-200:]}"
