"""
PDF Generator - Generates professional resume PDFs from ResumData objects.
Uses ReportLab for PDF creation with professional styling.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add parent directory to path for direct script execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from .styling import build_styles
from .components import hr, two_col_row, bullet_item, build_contact_line

logger = logging.getLogger(__name__)

# Handle imports for both module and script contexts
try:
    from ..resume_model import ResumData
except ImportError:
    from core.resume_model import ResumData


def generate_pdf(
    resume_data: ResumData,
    output_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Generate a professional resume PDF from ResumData.
    
    Args:
        resume_data: ResumData object containing all resume information
        output_path: Path to save the PDF file
        metadata: Optional metadata to embed (alteration type, intensity, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"🚀 Generating PDF: {output_path}")
        
        # Create document with metadata
        doc_metadata = {}
        if metadata:
            doc_metadata = {
                'title': metadata.get('title', 'Resume'),
                'author': resume_data.contact.name,
                'subject': metadata.get('subject', 'Professional Resume'),
                'creator': 'Beyond The Resume - AI Resume Optimizer',
                'producer': 'ReportLab',
            }
            # Add custom metadata
            if metadata.get('alteration_type'):
                doc_metadata['keywords'] = f"resume, {metadata['alteration_type']}"
            if metadata.get('generation_timestamp'):
                doc_metadata['creationDate'] = datetime.fromisoformat(metadata['generation_timestamp'])
        
        # Create document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=0.4 * inch,
            rightMargin=0.4 * inch,
            topMargin=0.15 * inch,
            bottomMargin=0.2 * inch,
            **doc_metadata
        )

        styles = build_styles()
        story = []

        # ── HEADER ────────────────────────────────────────────────────────────
        # Name
        story.append(Paragraph(resume_data.contact.name, styles["name"]))
        
        # Contact line with clickable links
        contact_line = build_contact_line(resume_data.contact)
        if contact_line:
            story.append(Paragraph(contact_line, styles["contact"]))
        
        # Summary (optional)
        if resume_data.summary:
            story.append(Paragraph("SUMMARY", styles["section_header"]))
            story.append(hr())
            story.append(Paragraph(resume_data.summary, styles["detail"]))
            story.append(Spacer(1, 3))

        # ── EDUCATION ─────────────────────────────────────────────────────────
        if resume_data.education:
            story.append(Paragraph("EDUCATION", styles["section_header"]))
            story.append(hr())
            
            for edu in resume_data.education:
                # School name on left, date on right
                date_str = edu.date or ""
                story.append(two_col_row(f"<b>{edu.school}</b>", date_str, styles, "school"))
                
                # Extract GPA from details
                gpa_str = ""
                other_details = []
                if edu.details:
                    for detail in edu.details:
                        detail_text = detail.get("text") if isinstance(detail, dict) else detail
                        if "GPA" in detail_text or "gpa" in detail_text:
                            gpa_str = detail_text
                        else:
                            other_details.append(detail_text)
                
                # Degree | GPA line
                degree_gpa = edu.degree
                if gpa_str:
                    degree_gpa += f" | {gpa_str}"
                story.append(Paragraph(degree_gpa, styles["detail"]))
                
                # Other details
                for detail in other_details:
                    story.append(Paragraph(detail, styles["detail"]))

        # ── SKILLS ────────────────────────────────────────────────────────────
        if resume_data.skills:
            story.append(Paragraph("SKILLS", styles["section_header"]))
            story.append(hr())
            
            for skill in resume_data.skills:
                if skill.items:
                    items_str = ", ".join(skill.items)
                    skill_line = f"<b>{skill.category}:</b> {items_str}"
                    story.append(bullet_item(skill_line, styles))
            
            story.append(Spacer(1, 3))

        # ── WORK EXPERIENCE ───────────────────────────────────────────────────
        if resume_data.work_experience:
            story.append(Paragraph("WORK EXPERIENCE", styles["section_header"]))
            story.append(hr())
            
            for job in resume_data.work_experience:
                # Title and company
                title_company = f"<b>{job.position}</b> – {job.company}"
                
                # Date
                date_parts = []
                if job.start_date:
                    date_parts.append(job.start_date)
                if job.end_date:
                    date_parts.append(job.end_date)
                date_str = " – ".join(date_parts) if date_parts else ""
                
                story.append(two_col_row(title_company, date_str, styles, "job_title"))
                
                # Bullets
                for bullet in job.bullets:
                    story.append(bullet_item(bullet.text, styles))
                
                story.append(Spacer(1, 3))

        # ── PROJECTS ──────────────────────────────────────────────────────────
        if resume_data.projects:
            story.append(Paragraph("PROJECTS", styles["section_header"]))
            story.append(hr())
            
            for project in resume_data.projects:
                # Project name and tech
                header = f"<b>{project.name}</b>"
                if project.technologies:
                    header += f" | {project.technologies}"
                
                # Date
                date_str = project.date or ""
                
                story.append(two_col_row(header, date_str, styles, "project_name"))
                
                # Bullets
                for bullet in project.bullets:
                    story.append(bullet_item(bullet.text, styles))
                
                story.append(Spacer(1, 3))

        # ── LEADERSHIP ────────────────────────────────────────────────────────
        if resume_data.leadership:
            story.append(Paragraph("LEADERSHIP", styles["section_header"]))
            story.append(hr())
            
            for lead in resume_data.leadership:
                # Title and organization
                header = f"<b>{lead.title}</b>"
                if lead.organization:
                    header += f" – {lead.organization}"
                
                # Date
                date_parts = []
                if lead.date:
                    date_parts.append(lead.date)
                date_str = date_parts[0] if date_parts else ""
                
                story.append(two_col_row(header, date_str, styles, "job_title"))
                
                # Bullets
                for bullet in lead.bullets:
                    story.append(bullet_item(bullet.text, styles))
                
                story.append(Spacer(1, 3))

        # ── CERTIFICATIONS ────────────────────────────────────────────────────
        if resume_data.certifications:
            story.append(Paragraph("CERTIFICATIONS", styles["section_header"]))
            story.append(hr())
            
            for cert in resume_data.certifications:
                cert_name = ""
                cert_date = ""
                
                if isinstance(cert, dict):
                    cert_name = cert.get("name", str(cert))
                    cert_date = cert.get("date", "")
                else:
                    cert_name = str(cert)
                
                story.append(two_col_row(cert_name, cert_date, styles, "detail"))

        # Build PDF
        doc.build(story)
        logger.info(f"✅ PDF generated successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generating PDF: {e}", exc_info=True)
        return False
