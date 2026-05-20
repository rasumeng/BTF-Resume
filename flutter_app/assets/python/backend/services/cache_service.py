"""
Cache Service - Manages parsed resume cache to avoid re-parsing.
Stores parsed resume structure locally for quick access.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CacheService:
    """Service for managing parsed resume cache."""
    
    # Cache file extension
    CACHE_EXTENSION = ".parsed.json"
    
    @staticmethod
    def get_cache_path(resume_path: Path) -> Path:
        """Get the cache file path for a resume."""
        return resume_path.parent / f"{resume_path.stem}{CacheService.CACHE_EXTENSION}"
    
    @staticmethod
    def save_parsed_resume(resume_path: Path, parsed_data: Dict) -> bool:
        """
        Save parsed resume to cache file.
        
        Args:
            resume_path: Path to the original resume file
            parsed_data: Parsed resume structure from LLM
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            cache_path = CacheService.get_cache_path(resume_path)
            
            # Add metadata
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "original_file": str(resume_path),
                "parsed_data": parsed_data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"✅ Cached parsed resume: {cache_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to cache parsed resume: {e}")
            return False
    
    @staticmethod
    def load_cached_resume(resume_path: Path) -> Optional[Dict]:
        """
        Load cached parsed resume if it exists.
        
        Args:
            resume_path: Path to the original resume file
            
        Returns:
            Cached parsed data if exists and valid, None otherwise
        """
        try:
            cache_path = CacheService.get_cache_path(resume_path)
            
            if not cache_path.exists():
                logger.debug(f"⏭️  No cache found for: {resume_path}")
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            parsed_data = cache_data.get("parsed_data")
            timestamp = cache_data.get("timestamp", "unknown")
            logger.info(f"✅ Loaded cached parsed resume (cached at {timestamp}): {cache_path}")
            return parsed_data
        except Exception as e:
            logger.error(f"❌ Failed to load cached resume: {e}")
            return None
    
    @staticmethod
    def invalidate_cache(resume_path: Path) -> bool:
        """
        Delete cache file for a resume.
        
        Args:
            resume_path: Path to the original resume file
            
        Returns:
            True if invalidated (or didn't exist), False on error
        """
        try:
            cache_path = CacheService.get_cache_path(resume_path)
            
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"🗑️  Invalidated cache: {cache_path}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to invalidate cache: {e}")
            return False
    
    @staticmethod
    def extract_resume_text_from_cache(parsed_data: Dict) -> str:
        """
        Reconstruct resume text from parsed cache for operations that need raw text.
        
        Args:
            parsed_data: Cached parsed resume structure
            
        Returns:
            Reconstructed resume text
        """
        try:
            lines = []
            
            # Add contact info
            contact = parsed_data.get("contact", {})
            if isinstance(contact, str):
                lines.append(contact)
            
            # Add name
            if parsed_data.get("name"):
                lines.append(f"\n{parsed_data['name']}")
            
            # Add education
            education = parsed_data.get("education", [])
            if education:
                lines.append("\nEDUCATION")
                for edu in education:
                    school = edu.get("school", "")
                    detail = edu.get("detail", "")
                    dates = edu.get("dates", "")
                    lines.append(f"{school} {dates}")
                    if detail:
                        lines.append(f"  {detail}")
            
            # Add technical skills
            skills = parsed_data.get("technical_skills", [])
            if skills:
                lines.append("\nTECHNICAL SKILLS")
                for skill_category in skills:
                    if isinstance(skill_category, list) and len(skill_category) >= 2:
                        category = skill_category[0]
                        items = skill_category[1]
                        lines.append(f"{category}: {items}")
            
            # Add work experience
            experience = parsed_data.get("work_experience", [])
            if experience:
                lines.append("\nWORK EXPERIENCE")
                for job in experience:
                    title = job.get("title", "")
                    company = job.get("company", "")
                    dates = job.get("dates", "")
                    lines.append(f"{title} – {company} {dates}")
                    for bullet in job.get("bullets", []):
                        lines.append(f"  - {bullet}")
            
            # Add projects
            projects = parsed_data.get("projects", [])
            if projects:
                lines.append("\nPROJECTS")
                for proj in projects:
                    name = proj.get("name", "")
                    tech = proj.get("tech", "")
                    lines.append(f"{name} | {tech}")
                    for bullet in proj.get("bullets", []):
                        lines.append(f"  - {bullet}")
            
            # Add leadership
            leadership = parsed_data.get("leadership", [])
            if leadership:
                lines.append("\nLEADERSHIP")
                for role in leadership:
                    title = role.get("title", "")
                    org = role.get("org", "")
                    dates = role.get("dates", "")
                    lines.append(f"{title} – {org} {dates}")
                    for bullet in role.get("bullets", []):
                        lines.append(f"  - {bullet}")
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"❌ Failed to extract text from cache: {e}")
            return ""
