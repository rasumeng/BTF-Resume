"""
Prompts module - Organized LLM prompt templates.
Imports all prompt functions for backward compatibility and convenience.
"""

from .bullet_prompts import bullet_polish_prompt, experience_updater_prompt
from .resume_prompts import resume_polish_prompt, get_changes_summary_prompt
from .job_prompts import job_tailor_prompt
from .grading_prompts import get_grader_prompt
from .parsing_prompts import (
    parse_resume_structure_prompt,
    parse_to_pdf_format_prompt,
    parse_resume_to_pdf_format_prompt,
)

__all__ = [
    # Bullet-level prompts
    "bullet_polish_prompt",
    "experience_updater_prompt",
    # Resume-level prompts
    "resume_polish_prompt",
    "get_changes_summary_prompt",
    # Job tailoring prompts
    "job_tailor_prompt",
    # Grading prompts
    "get_grader_prompt",
    # Parsing prompts
    "parse_resume_structure_prompt",
    "parse_to_pdf_format_prompt",
    "parse_resume_to_pdf_format_prompt",
]
