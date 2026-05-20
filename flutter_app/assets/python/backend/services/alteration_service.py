"""
Alteration Service - Manages resume polish/tailor operations with versioning.

Responsibilities:
- Full lifecycle management of resume alterations (parse → modify → generate → store)
- Version history tracking
- Metadata embedding
- State management (draft, saved, preview-ready)
- Fallback formats (text + PDF)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

from config import get_resumes_dir


@dataclass
class AlterationMetadata:
    """Metadata for a single alteration operation"""
    alteration_id: str  # UUID
    alteration_type: str  # 'polish' | 'tailor'
    timestamp: str  # ISO 8601
    intensity: Optional[str] = None  # For polish: 'light' | 'medium' | 'heavy'
    job_description: Optional[str] = None  # For tailor
    original_file: Optional[str] = None
    output_pdf: Optional[str] = None
    output_text: Optional[str] = None
    parsed_json: Optional[Dict] = None
    status: str = "draft"  # 'draft' | 'saved' | 'archived'
    preview_available: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        return asdict(self)


@dataclass
class AlterationHistory:
    """Complete history of alterations for a resume"""
    original_file: str
    created_at: str  # When history file was created
    alterations: List[AlterationMetadata]
    
    def to_dict(self) -> dict:
        return {
            "original_file": self.original_file,
            "created_at": self.created_at,
            "alterations": [a.to_dict() for a in self.alterations]
        }


class AlterationService:
    """Service for managing resume alterations with full lifecycle support."""
    
    @staticmethod
    def create_alteration_metadata(
        alteration_type: str,
        original_file: str,
        intensity: Optional[str] = None,
        job_description: Optional[str] = None
    ) -> AlterationMetadata:
        """Create metadata for a new alteration operation."""
        import uuid
        return AlterationMetadata(
            alteration_id=str(uuid.uuid4()),
            alteration_type=alteration_type,
            timestamp=datetime.utcnow().isoformat(),
            intensity=intensity,
            job_description=job_description,
            original_file=original_file,
        )
    
    @staticmethod
    def save_alteration_text(
        text_content: str,
        alteration_type: str,
        original_filename: str,
        intensity: Optional[str] = None
    ) -> str:
        """
        Save polished/tailored resume as text file.
        This is a fallback format before PDF generation.
        
        Returns:
            Filename of saved text file
        """
        try:
            resumes_dir = get_resumes_dir()
            
            # Generate filename: polished_{intensity}_{original}_{timestamp}.txt
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = original_filename.replace('.pdf', '').replace('.txt', '')
            
            if alteration_type == 'polish':
                text_filename = f"polished_{intensity}_{base_name}_{timestamp}.txt"
            elif alteration_type == 'tailor':
                text_filename = f"tailored_{base_name}_{timestamp}.txt"
            else:
                text_filename = f"altered_{alteration_type}_{base_name}_{timestamp}.txt"
            
            text_path = resumes_dir / text_filename
            
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logger.info(f"✓ Saved alteration text: {text_filename}")
            return text_filename
            
        except Exception as e:
            logger.error(f"✗ Error saving alteration text: {e}")
            raise
    
    @staticmethod
    def cache_parsed_structure(
        parsed_json: Dict,
        text_filename: str
    ) -> None:
        """
        Cache the parsed resume structure to avoid re-parsing.
        Stores as .json file alongside the text version.
        """
        try:
            resumes_dir = get_resumes_dir()
            json_filename = text_filename.replace('.txt', '.json')
            json_path = resumes_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_json, f, indent=2)
            
            logger.info(f"✓ Cached parsed structure: {json_filename}")
            
        except Exception as e:
            logger.error(f"⚠️  Failed to cache parsed structure: {e}")
            # Non-critical, don't raise
    
    @staticmethod
    def load_history(original_filename: str) -> Optional[AlterationHistory]:
        """
        Load alteration history for a resume.
        History is stored as {original_name}.history.json
        """
        try:
            resumes_dir = get_resumes_dir()
            history_filename = original_filename.replace('.pdf', '').replace('.txt', '') + '.history.json'
            history_path = resumes_dir / history_filename
            
            if not history_path.exists():
                logger.debug(f"No history file found: {history_filename}")
                return None
            
            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to AlterationHistory object
            alterations = [
                AlterationMetadata(**alt) for alt in data.get('alterations', [])
            ]
            
            return AlterationHistory(
                original_file=data['original_file'],
                created_at=data['created_at'],
                alterations=alterations
            )
            
        except Exception as e:
            logger.error(f"✗ Error loading history: {e}")
            return None
    
    @staticmethod
    def save_history(history: AlterationHistory, original_filename: str) -> None:
        """Save alteration history to disk."""
        try:
            resumes_dir = get_resumes_dir()
            history_filename = original_filename.replace('.pdf', '').replace('.txt', '') + '.history.json'
            history_path = resumes_dir / history_filename
            
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history.to_dict(), f, indent=2)
            
            logger.info(f"✓ Saved alteration history: {history_filename}")
            
        except Exception as e:
            logger.error(f"✗ Error saving history: {e}")
            raise
    
    @staticmethod
    def add_alteration_to_history(
        original_filename: str,
        metadata: AlterationMetadata
    ) -> AlterationHistory:
        """
        Add a new alteration to the history file.
        Creates history file if it doesn't exist.
        """
        try:
            # Load existing history or create new
            history = AlterationService.load_history(original_filename)
            
            if history is None:
                history = AlterationHistory(
                    original_file=original_filename,
                    created_at=datetime.utcnow().isoformat(),
                    alterations=[]
                )
            
            # Add new alteration
            history.alterations.append(metadata)
            
            # Save updated history
            AlterationService.save_history(history, original_filename)
            
            logger.info(f"✓ Added alteration to history: {original_filename}")
            return history
            
        except Exception as e:
            logger.error(f"✗ Error adding to history: {e}")
            raise
    
    @staticmethod
    def get_alteration_stats(original_filename: str) -> Dict:
        """Get statistics about alterations for a resume."""
        try:
            history = AlterationService.load_history(original_filename)
            
            if not history:
                return {"total_alterations": 0, "by_type": {}}
            
            stats = {
                "total_alterations": len(history.alterations),
                "by_type": {},
                "latest_alteration": None,
                "history_created": history.created_at
            }
            
            for alt in history.alterations:
                alt_type = alt.alteration_type
                stats["by_type"][alt_type] = stats["by_type"].get(alt_type, 0) + 1
            
            if history.alterations:
                latest = history.alterations[-1]
                stats["latest_alteration"] = {
                    "type": latest.alteration_type,
                    "timestamp": latest.timestamp,
                    "status": latest.status
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"✗ Error getting alteration stats: {e}")
            return {"error": str(e)}
