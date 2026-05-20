"""
PDF Generator - Works with ResumData Model

Generates professional resume PDFs from ResumData objects.
Uses Jake's Resume template styling with ReportLab.
"""

import sys
from pathlib import Path

# Add parent directory to path for direct script execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Handle imports for both module and script contexts
try:
    from .resume_model import ResumData
except ImportError:
    from core.resume_model import ResumData


def build_styles():
    """Build and return ReportLab styles for resume."""
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


def build_contact_line(contact) -> str:
    """Build contact line with clickable links for email, LinkedIn, GitHub.
    Links display in Google Docs blue, other text in black."""
    parts = []
    
    if contact.phone:
        parts.append(f'<font color="black">{contact.phone}</font>')
    
    if contact.email:
        parts.append(f'<a href="mailto:{contact.email}"><font color="#0563C1">{contact.email}</font></a>')
    
    # Only include location if it has meaningful content
    if contact.location and contact.location.strip() and "not" not in contact.location.lower():
        parts.append(f'<font color="black">{contact.location}</font>')
    
    if contact.linkedin:
        url = contact.linkedin if contact.linkedin.startswith("http") else f"https://{contact.linkedin}"
        # Remove https:// for display
        display_text = url.replace("https://", "").replace("http://", "")
        parts.append(f'<a href="{url}"><font color="#0563C1">{display_text}</font></a>')
    
    if contact.github:
        url = contact.github if contact.github.startswith("http") else f"https://{contact.github}"
        # Remove https:// for display
        display_text = url.replace("https://", "").replace("http://", "")
        parts.append(f'<a href="{url}"><font color="#0563C1">{display_text}</font></a>')
    
    # Add other websites
    for key, url in (contact.websites or {}).items():
        parts.append(f'<a href="{url}"><font color="#0563C1">{key}</font></a>')
    
    return " | ".join(parts)


def hr():
    """Create horizontal rule."""
    return HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=3, spaceBefore=1)


def two_col_row(left_text: str, right_text: str, styles: dict, left_style_key: str = "job_title"):
    """Create a two-column table row (left: content, right: date/location)."""
    right_style = ParagraphStyle(
        "RightDate",
        fontName="Times-Bold",
        fontSize=11,
        alignment=TA_RIGHT,
    )
    
    left_para = Paragraph(left_text, styles[left_style_key])
    right_para = Paragraph(right_text, right_style)
    
    table = Table([[left_para, right_para]], colWidths=["70%", "30%"])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def bullet_item(text: str, styles: dict) -> Paragraph:
    """Create a bullet point."""
    return Paragraph(f"• {text}", styles["bullet"])


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


if __name__ == "__main__":
    """
    Test the PDF generator directly with sample data.
    Run with: python core/pdf_generator.py
    """
    import sys
    from pathlib import Path
    
    # Handle imports when running as __main__
    try:
        from .resume_model import ResumData, ContactInfo, WorkExperience, Project, Education, Leadership, Skill
        from .utils import BulletPoint
    except ImportError:
        # Fallback for when running as script
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from core.resume_model import ResumData, ContactInfo, WorkExperience, Project, Education, Leadership, Skill
        from core.utils import BulletPoint
    
    # Create sample resume data for testing/fine-tuning
    sample_resume = ResumData(
        contact=ContactInfo(
            name="Robert Asumeng",
            email="robert@example.com",
            phone="(555) 123-4567",
            location="San Francisco, CA",
            linkedin="https://linkedin.com/in/robert",
            github="https://github.com/robert"
        ),
        summary="Results-driven software engineer with 5+ years of experience building scalable applications and leading technical initiatives.",
        work_experience=[
            WorkExperience(
                position="Senior Software Engineer",
                company="TechCorp",
                location="San Francisco, CA",
                start_date="Jan 2021",
                end_date="Present",
                bullets=[
                    BulletPoint(text="Led development of microservices architecture using Python and Django, improving system performance by 40%"),
                    BulletPoint(text="Implemented CI/CD pipeline using GitHub Actions, reducing deployment time from 2 hours to 15 minutes"),
                    BulletPoint(text="Mentored 3 junior developers, conducting weekly code reviews and technical training sessions"),
                    BulletPoint(text="Optimized database queries, reducing API response time from 500ms to 50ms")
                ]
            ),
            WorkExperience(
                position="Software Developer",
                company="StartupInc",
                location="Remote",
                start_date="June 2019",
                end_date="Dec 2020",
                bullets=[
                    BulletPoint(text="Built RESTful APIs using Flask and PostgreSQL serving 1M+ requests daily"),
                    BulletPoint(text="Developed real-time data processing pipeline using Apache Kafka and Python"),
                    BulletPoint(text="Contributed to open-source projects with 500+ GitHub stars"),
                    BulletPoint(text="Implemented automated testing suite achieving 85% code coverage")
                ]
            )
        ],
        projects=[
            Project(
                name="Resume AI System",
                date="Jan 2024 – Present",
                technologies="Python, Flask, ReportLab, Ollama",
                bullets=[
                    BulletPoint(text="Built full-stack resume optimization platform with PDF generation capabilities"),
                    BulletPoint(text="Implemented LLM-based resume parsing and polishing features"),
                    BulletPoint(text="Created professional PDF generation with ReportLab template system"),
                    BulletPoint(text="Achieved 95% accuracy in extracting resume data from various formats")
                ]
            ),
            Project(
                name="Open Source Contribution – PyData",
                date="May 2021 – Present",
                technologies="Python, NumPy, Pandas, GitHub",
                bullets=[
                    BulletPoint(text="Contributed 50+ code commits improving data processing efficiency"),
                    BulletPoint(text="Maintained backward compatibility while refactoring core modules"),
                    BulletPoint(text="Collaborated with 20+ developers across 8 countries")
                ]
            )
        ],
        education=[
            Education(
                degree="Bachelor of Science in Computer Science",
                school="State University",
                location="San Francisco, CA",
                date="May 2019",
                details=[
                    "GPA: 3.8/4.0",
                    "Dean's List all semesters",
                    "Relevant Coursework: Data Structures, Algorithms, Database Design, Software Engineering"
                ]
            )
        ],
        leadership=[
            Leadership(
                title="Tech Lead",
                organization="Developer Community",
                location="San Francisco, CA",
                date="Jan 2022 – Present",
                bullets=[
                    BulletPoint(text="Organized monthly meetups for 100+ software engineers"),
                    BulletPoint(text="Led technical workshops on Python best practices and system design"),
                    BulletPoint(text="Built community Slack workspace with 500+ active members")
                ]
            )
        ],
        skills=[
            Skill(category="Programming Languages", items=["Python", "JavaScript", "SQL", "Go"]),
            Skill(category="Web Frameworks", items=["Django", "Flask", "FastAPI", "React"]),
            Skill(category="Databases", items=["PostgreSQL", "MongoDB", "Redis"]),
            Skill(category="DevOps", items=["Docker", "Kubernetes", "GitHub Actions", "AWS"])
        ],
        certifications=[
            {"name": "AWS Certified Solutions Architect", "date": "2022"},
            {"name": "Python Developer Certification", "date": "2021"}
        ]
    )
    
    # Generate test PDF
    output_path = Path(__file__).parent.parent / "outputs" / "test_formatting.pdf"
    output_path.parent.mkdir(exist_ok=True)
    
    print(f"🎨 Generating test PDF for formatting fine-tuning...")
    print(f"Output: {output_path}")
    
    success = generate_pdf(sample_resume, str(output_path))
    
    if success:
        print(f"✅ Test PDF created successfully!")
        print(f"📄 Open: {output_path}")
        print(f"\n💡 Tips for fine-tuning:")
        print(f"   - Adjust font sizes in build_styles()")
        print(f"   - Modify spacing/margins in the generate_pdf() function")
        print(f"   - Change colors in the styling definitions")
        print(f"   - Adjust bullet point indentation and line spacing")
    else:
        print(f"❌ Failed to generate test PDF")
