"""
Resume Data Models
==================
Pydantic schemas for resume parsing results, resume sections,
and the upload response returned to the client.
"""

from pydantic import BaseModel, Field


class ResumeSection(BaseModel):
    """
    A single detected section of a resume (e.g., "Experience", "Education").

    Attributes:
        name:    The section heading as detected (e.g., "Work Experience").
        content: The raw text content under this section.
    """
    name: str = Field(..., description="Section heading (e.g., 'Experience', 'Education')")
    content: str = Field(..., description="Raw text content of the section")


class ResumeData(BaseModel):
    """
    Fully parsed resume data extracted from a PDF or DOCX file.

    Attributes:
        raw_text:           The full text extracted from the document.
        sections:           List of detected resume sections.
        contact_info:       Detected contact information (name, email, phone, etc.).
        detected_skills:    Skills extracted from the resume text.
        formatting_issues:  List of formatting problems that affect ATS parsing.
        file_type:          Original file type ('pdf' or 'docx').
    """
    raw_text: str = Field(..., description="Complete extracted text from the resume")
    sections: list[ResumeSection] = Field(default_factory=list, description="Detected resume sections")
    contact_info: dict[str, str] = Field(default_factory=dict, description="Contact info (name, email, phone, linkedin)")
    detected_skills: list[str] = Field(default_factory=list, description="Skills found in the resume")
    formatting_issues: list[str] = Field(default_factory=list, description="ATS formatting warnings")
    file_type: str = Field(..., description="File type: 'pdf' or 'docx'")


class ResumeUploadResponse(BaseModel):
    """
    Response returned after a resume file is uploaded and parsed.

    Attributes:
        success:     Whether parsing succeeded.
        message:     Human-readable status message.
        resume_data: The parsed resume data (None if parsing failed).
    """
    success: bool = Field(..., description="Whether the resume was parsed successfully")
    message: str = Field(..., description="Status message")
    resume_data: ResumeData | None = Field(None, description="Parsed resume data")
