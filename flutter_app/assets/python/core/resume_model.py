"""
Resume Data Model

Defines the structured schema for resume data with validation.
This ensures consistent data storage across parsing and generation.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from .utils import create_bullet_points, BulletPoint


@dataclass
class ContactInfo:
    """Contact information at the top of resume"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    websites: Dict[str, str] = field(default_factory=dict)  # {name: url}
    
    def to_dict(self) -> dict:
        """Convert to dict, excluding None values"""
        data = asdict(self)
        return {k: v for k, v in data.items() if v}
    
    @classmethod
    def from_dict(cls, data: dict) -> "ContactInfo":
        """Create from dict, handling extra fields
        
        Note: Does NOT set name to "Resume" - that's handled by from_llm_json()
        to allow better error checking and fallback behavior.
        """
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields and v}
        
        # Ensure name is at least an empty string (required field)
        if "name" not in filtered:
            filtered["name"] = ""
        
        return cls(**filtered)
    
    def get_contact_line(self) -> str:
        """Generate formatted contact line for resume header"""
        parts = []
        if self.phone:
            parts.append(self.phone)
        if self.email:
            parts.append(self.email)
        if self.location:
            parts.append(self.location)
        if self.linkedin:
            # Extract just the URL or username
            parts.append(self.linkedin)
        if self.github:
            parts.append(self.github)
        
        # Add other websites
        for key, url in (self.websites or {}).items():
            parts.append(url)
        
        return " | ".join(parts)


@dataclass
class WorkExperience:
    """Work experience entry"""
    position: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullets: List[BulletPoint] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "position": self.position,
            "company": self.company,
            "location": self.location,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "bullets": [asdict(b) for b in self.bullets] if self.bullets else [],
        }


@dataclass
class Project:
    """Project entry"""
    name: str
    location: Optional[str] = None
    date: Optional[str] = None
    technologies: Optional[str] = None
    bullets: List[BulletPoint] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "location": self.location,
            "date": self.date,
            "technologies": self.technologies,
            "bullets": [asdict(b) for b in self.bullets] if self.bullets else [],
        }


@dataclass
class Education:
    """Education entry"""
    degree: str
    school: str
    location: Optional[str] = None
    date: Optional[str] = None
    details: List[Dict] = field(default_factory=list)  # [{text: str}]
    
    def to_dict(self) -> dict:
        return {
            "degree": self.degree,
            "school": self.school,
            "location": self.location,
            "date": self.date,
            "details": self.details if self.details else [],
        }


@dataclass
class Leadership:
    """Leadership/Activities entry"""
    title: str
    organization: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    bullets: List[BulletPoint] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "organization": self.organization,
            "location": self.location,
            "date": self.date,
            "bullets": [asdict(b) for b in self.bullets] if self.bullets else [],
        }


@dataclass
class Skill:
    """Skill category"""
    category: str
    items: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "items": self.items if self.items else [],
        }


@dataclass
class ResumData:
    """Complete resume structure"""
    contact: ContactInfo
    work_experience: List[WorkExperience] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    leadership: List[Leadership] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    certifications: Optional[List[Dict]] = None
    summary: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        data = {
            "contact": self.contact.to_dict(),
            "work_experience": [e.to_dict() for e in self.work_experience],
            "projects": [p.to_dict() for p in self.projects],
            "education": [e.to_dict() for e in self.education],
            "leadership": [l.to_dict() for l in self.leadership],
            "skills": [s.to_dict() for s in self.skills],
        }
        if self.certifications:
            data["certifications"] = self.certifications
        if self.summary:
            data["summary"] = self.summary
        return data
    
    @classmethod
    def from_llm_json(cls, llm_json: dict) -> "ResumData":
        """Create ResumData from LLM-generated JSON
        
        Handles the raw JSON output from the LLM parser and converts it
        to structured ResumData objects with validation.
        
        Robust parsing that handles various formats the LLM might return.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract contact info - with robust handling
        contact_raw = llm_json.get("contact", {})
        if isinstance(contact_raw, str):
            contact_raw = {"name": contact_raw}
        elif not isinstance(contact_raw, dict):
            contact_raw = {}
        
        # Ensure contact dict has required fields
        contact = ContactInfo.from_dict(contact_raw)
        if not contact.name or contact.name == "Resume":
            # Try to extract name from other locations
            potential_name = llm_json.get("name")
            if potential_name and isinstance(potential_name, str):
                contact.name = potential_name
            else:
                contact.name = "Resume"
        
        logger.info(f"📝 Parsed contact name: {contact.name}")
        
        # Helper function to convert bullet strings to BulletPoint-compatible dicts
        def _normalize_bullets(bullets_raw):
            """Convert raw bullets (strings or dicts) to proper format"""
            result = []
            if isinstance(bullets_raw, str):
                bullets_raw = [bullets_raw]
            elif not isinstance(bullets_raw, list):
                bullets_raw = []
            
            for bullet in bullets_raw:
                if isinstance(bullet, str):
                    # Convert string to dict format
                    result.append({"text": bullet.strip()})
                elif isinstance(bullet, dict):
                    # Keep dict but ensure it has 'text' key
                    if "text" not in bullet:
                        # If no 'text' key, assume the dict value is the text
                        result.append({"text": str(bullet.get("bullet", "")).strip()})
                    else:
                        result.append(bullet)
            return result
        
        # Extract work experience - robust parsing
        work_exp = []
        work_exp_data = llm_json.get("work_experience", [])
        
        # Handle both list and dict formats
        if isinstance(work_exp_data, dict):
            work_exp_data = [work_exp_data]
        elif not isinstance(work_exp_data, list):
            work_exp_data = []
        
        for item in work_exp_data:
            if not isinstance(item, dict):
                continue
            
            # Extract and normalize bullets
            bullets_normalized = _normalize_bullets(item.get("bullets", []))
            
            work_exp.append(WorkExperience(
                position=str(item.get("position", "")).strip(),
                company=str(item.get("company", "")).strip(),
                location=item.get("location"),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
                bullets=create_bullet_points(bullets_normalized),
            ))
        
        logger.info(f"📋 Parsed {len(work_exp)} work experience entries")
        
        # Extract projects - robust parsing
        projects = []
        projects_data = llm_json.get("projects", [])
        
        if isinstance(projects_data, dict):
            projects_data = [projects_data]
        elif not isinstance(projects_data, list):
            projects_data = []
        
        for item in projects_data:
            if not isinstance(item, dict):
                continue
            
            # Extract and normalize bullets
            bullets_normalized = _normalize_bullets(item.get("bullets", []))
            
            projects.append(Project(
                name=str(item.get("name", "")).strip(),
                location=item.get("location"),
                date=item.get("date"),
                technologies=item.get("technologies"),
                bullets=create_bullet_points(bullets_normalized),
            ))
        
        logger.info(f"🚀 Parsed {len(projects)} projects")
        
        # Extract education - robust parsing
        education = []
        education_data = llm_json.get("education", [])
        
        if isinstance(education_data, dict):
            education_data = [education_data]
        elif not isinstance(education_data, list):
            education_data = []
        
        for item in education_data:
            if not isinstance(item, dict):
                continue
            
            education.append(Education(
                degree=str(item.get("degree", "")).strip(),
                school=str(item.get("school", "")).strip(),
                location=item.get("location"),
                date=item.get("date"),
                details=item.get("details", []),
            ))
        
        logger.info(f"🎓 Parsed {len(education)} education entries")
        
        # Extract leadership - robust parsing
        leadership = []
        leadership_data = llm_json.get("leadership", [])
        
        if isinstance(leadership_data, dict):
            leadership_data = [leadership_data]
        elif not isinstance(leadership_data, list):
            leadership_data = []
        
        for item in leadership_data:
            if not isinstance(item, dict):
                continue
            
            # Extract and normalize bullets
            bullets_normalized = _normalize_bullets(item.get("bullets", []))
            
            leadership.append(Leadership(
                title=str(item.get("title", "")).strip(),
                organization=item.get("organization"),
                location=item.get("location"),
                date=item.get("date"),
                bullets=create_bullet_points(bullets_normalized),
            ))
        
        logger.info(f"👥 Parsed {len(leadership)} leadership entries")
        
        # Extract skills - robust parsing
        skills = []
        skills_data = llm_json.get("skills", [])
        
        if isinstance(skills_data, dict):
            skills_data = [skills_data]
        elif not isinstance(skills_data, list):
            skills_data = []
        
        for item in skills_data:
            if not isinstance(item, dict):
                continue
            
            items_raw = item.get("items", [])
            if isinstance(items_raw, str):
                items_raw = [items_raw]
            elif not isinstance(items_raw, list):
                items_raw = []
            
            skills.append(Skill(
                category=str(item.get("category", "")).strip(),
                items=[str(i).strip() for i in items_raw if i],
            ))
        
        logger.info(f"💡 Parsed {len(skills)} skill categories")
        
        logger.info(f"✅ ResumData created successfully for {contact.name}")
        
        return cls(
            contact=contact,
            work_experience=work_exp,
            projects=projects,
            education=education,
            leadership=leadership,
            skills=skills,
            certifications=llm_json.get("certifications"),
            summary=llm_json.get("summary"),
        )
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate resume data. Returns (is_valid, list_of_errors)"""
        errors = []
        
        # Contact validation
        if not self.contact or not self.contact.name:
            errors.append("Contact name is required")
        if not self.contact.email and not self.contact.phone:
            errors.append("At least email or phone is required")
        
        # Section validation (at least one section should exist)
        has_sections = (
            self.work_experience or
            self.projects or
            self.education or
            self.leadership or
            self.skills
        )
        if not has_sections:
            errors.append("Resume must have at least one section (work, projects, education, etc.)")
        
        return len(errors) == 0, errors
