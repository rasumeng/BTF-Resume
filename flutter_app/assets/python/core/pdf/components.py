"""
PDF components - Reusable ReportLab components for resume layout.
"""

from reportlab.platypus import HRFlowable, Table, TableStyle, Paragraph, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT


def hr() -> HRFlowable:
    """Create a horizontal rule element."""
    return HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=3, spaceBefore=1)


def two_col_row(left_text: str, right_text: str, styles: dict, left_style_key: str = "job_title") -> Table:
    """
    Create a two-column table row (left: content, right: date/location).
    
    Args:
        left_text: Content for left column (e.g., job title)
        right_text: Content for right column (e.g., date)
        styles: Dictionary of ParagraphStyle objects
        left_style_key: Style key to use for left column
        
    Returns:
        ReportLab Table element
    """
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
    """
    Create a bullet point paragraph.
    
    Args:
        text: Bullet text
        styles: Dictionary of ParagraphStyle objects
        
    Returns:
        Paragraph with bullet formatting
    """
    return Paragraph(f"• {text}", styles["bullet"])


def build_contact_line(contact) -> str:
    """
    Build contact information line with clickable links.
    
    Links display in Google Docs blue, other text in black.
    
    Args:
        contact: ContactInfo object
        
    Returns:
        HTML-formatted contact string with links
    """
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
