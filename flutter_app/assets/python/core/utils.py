"""
Common utilities and helpers to reduce redundancy across core modules.
"""

import json
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


# Error messages
OLLAMA_ERROR_MESSAGES = {
    "model_not_loaded": "❌ ERROR: Failed to get response from {model} (model may not be loaded)\n"
                       "❌ TIP: Check that {model} is loaded in Ollama by visiting http://localhost:11434/api/tags\n"
                       "❌ To load {model}, run: ollama pull {model}",
    "connection_failed": "❌ Cannot connect to Ollama at http://localhost:11434\n"
                        "❌ Make sure Ollama is running. Start it with: ollama serve",
    "timeout": "❌ Timeout waiting for Ollama to respond (model: {model}, timeout: {timeout}s)\n"
              "❌ This often means the model is still loading or system is slow.",
    "not_found": "Error from Ollama: Model '{model}' not found or not loaded\n"
                "Available models can be checked at: http://localhost:11434/api/tags\n"
                "Load the model with: ollama pull {model}",
}




def normalize_whitespace(text: str) -> str:
    """Remove excess whitespace from text."""
    return re.sub(r"\s+", " ", text.strip())


def extract_urls(text: str) -> dict:
    """
    Extract common URLs from text (email, phone, LinkedIn, GitHub).
    
    Returns dict with keys: email, phone, linkedin, github
    """
    urls = {
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
    }
    
    # Email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        urls["email"] = email_match.group(0)
    
    # Phone
    phone_match = re.search(r"(?:\+\d{1,3}[-.\s]?)?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})", text)
    if phone_match:
        urls["phone"] = phone_match.group(0).strip()
    
    # LinkedIn
    linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-\.]+/?", text, re.IGNORECASE)
    if linkedin_match:
        url = linkedin_match.group(0).rstrip("/")
        if not url.startswith("http"):
            url = "https://" + url
        urls["linkedin"] = url
    
    # GitHub
    github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w\-\.]+/?", text, re.IGNORECASE)
    if github_match:
        url = github_match.group(0).rstrip("/")
        if not url.startswith("http"):
            url = "https://" + url
        urls["github"] = url
    
    return urls


@dataclass
class BulletPoint:
    """A single resume bullet point"""
    text: str
    has_location: bool = False
    has_date: bool = False


def create_bullet_points(bullets_data: List[Dict[str, Any]]) -> List[BulletPoint]:
    """
    Convert bullet data to BulletPoint objects.
    
    Args:
        bullets_data: List of dicts with bullet information
        
    Returns:
        List of BulletPoint objects
    """
    result = []
    
    if not isinstance(bullets_data, list):
        return result
    
    for bullet in bullets_data:
        if isinstance(bullet, dict):
            text = bullet.get("text", "").strip()
            if text:
                result.append(BulletPoint(
                    text=text,
                    has_location=bullet.get("has_location", False),
                    has_date=bullet.get("has_date", False)
                ))
        elif isinstance(bullet, str):
            # Simple string bullet
            text = bullet.strip()
            if text:
                result.append(BulletPoint(text=text))
    
    return result
