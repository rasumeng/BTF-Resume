"""
PDF styling - ReportLab paragraph styles for resume components.
"""

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors


def build_styles() -> dict:
    """
    Build and return ReportLab styles for resume.
    
    Returns:
        Dictionary of ParagraphStyle objects keyed by component name
    """
    base_font = "Times-Roman"
    base_bold = "Times-Bold"
    fs = 11  # base font size

    return {
        "name": ParagraphStyle(
            "Name",
            fontName=base_bold,
            fontSize=13,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "contact": ParagraphStyle(
            "Contact",
            fontName=base_font,
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "section_header": ParagraphStyle(
            "SectionHeader",
            fontName=base_bold,
            fontSize=11,
            spaceBefore=0,
            spaceAfter=3,
            textColor=colors.black,
        ),
        "school": ParagraphStyle(
            "School",
            fontName=base_bold,
            fontSize=fs,
            spaceAfter=0,
        ),
        "detail": ParagraphStyle(
            "Detail",
            fontName=base_font,
            fontSize=fs,
            spaceAfter=3,
        ),
        "job_title": ParagraphStyle(
            "JobTitle",
            fontName=base_bold,
            fontSize=fs,
            spaceAfter=0,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName=base_font,
            fontSize=fs,
            leftIndent=7,
            firstLineIndent=-6,
            spaceAfter=3,
            leading=13,
        ),
        "skill_bullet": ParagraphStyle(
            "SkillBullet",
            fontName=base_font,
            fontSize=fs,
            leftIndent=7,
            spaceAfter=3,
            leading=13,
        ),
        "project_name": ParagraphStyle(
            "ProjectName",
            fontName=base_bold,
            fontSize=fs,
            spaceAfter=0,
        ),
    }
