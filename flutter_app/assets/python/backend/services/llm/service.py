"""
LLM Service - Handles all LLM calls for resume processing.
Uses the initialized Ollama service via Flask request context.
"""

import logging
import traceback
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

from .parsers import (
    extract_json_from_response,
    extract_bullet_list,
    extract_grade_data,
    validate_parsed_resume,
)


def _get_ollama_service():
    """
    Centralized Ollama service getter. Handles both request-context and fallback cases.
    
    Tries to get the service from Flask request context (g.ollama_service) first,
    then falls back to the singleton instance if not in a request context.
    
    Returns:
        OllamaService: The singleton Ollama service instance.
    """
    try:
        from flask import g, has_request_context
        if has_request_context() and hasattr(g, 'ollama_service'):
            return g.ollama_service
    except (ImportError, RuntimeError):
        pass
    
    # Fallback to singleton instance
    from ..ollama_service import get_ollama_service
    return get_ollama_service()


class LLMService:
    """Service for LLM-powered resume operations."""
    
    @staticmethod
    def call_ollama(prompt: str, stream: bool = False) -> Optional[str]:
        """
        Call Ollama LLM with a prompt and return the response text.
        
        Args:
            prompt: The prompt to send to Ollama
            stream: Whether to stream the response
            
        Returns:
            The response text from Ollama, or None if it fails
        """
        try:
            ollama = _get_ollama_service()
            result = ollama.generate(prompt, stream=stream)
            
            if not result.get("success"):
                error_msg = result.get("error", "No response from Ollama")
                logger.error(f"✗ Ollama generation failed: {error_msg}")
                return None
            
            response = result.get("data", {}).get("response", "")
            if not response:
                logger.error("✗ No response text received from Ollama")
                return None
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"✗ Error calling Ollama: {e}")
            return None
    
    @staticmethod
    def polish_bullets(bullets: List[str], intensity: str = "medium") -> Dict:
        """
        Polish resume bullets to be stronger and ATS-optimized.
        
        Args:
            bullets: List of bullet points to polish
            intensity: 'light', 'medium', or 'heavy'
            
        Returns:
            Dict with success status and polished bullets
        """
        try:
            ollama = _get_ollama_service()
            
            # Build prompt for polishing
            prompt = f"""You are an expert resume writer. Rewrite these resume bullets to be:
- Stronger and more impactful
- ATS-optimized (include metrics and keywords)
- Concise but comprehensive
- Intensity level: {intensity}

Bullets:
{chr(10).join(f'- {b}' for b in bullets)}

Return ONLY valid JSON array of polished bullets, like ["bullet1", "bullet2", ...].
DO NOT include any markdown, code blocks, or explanations. Just the JSON array."""
            
            logger.info("✨ Polishing bullets using Ollama...")
            result = ollama.generate(prompt, stream=False)
            
            if not result.get("success"):
                error_msg = result.get("error", "No response from Ollama. Please try again.")
                logger.error(f"✗ Ollama generation failed: {error_msg}")
                return {"success": False, "error": error_msg}
            
            response = result.get("data", {}).get("response", "")
            
            if not response:
                logger.error("✗ No response text received from Ollama")
                return {"success": False, "error": "No text response from Ollama. Please try again."}
            
            logger.debug(f"Raw Ollama response: {response[:500]}")
            
            # Parse response and extract bullet list
            polished_bullets = extract_bullet_list(response)
            
            if polished_bullets and len(polished_bullets) > 0:
                logger.info(f"✓ Got {len(polished_bullets)} polished bullets")
                return {"success": True, "bullets": polished_bullets}
            
            # Fallback: if we got a single response, treat as one polished bullet
            if response and len(response) > 10:
                logger.warning("⚠️  Could not parse JSON response, returning raw response as single bullet")
                return {"success": True, "bullets": [response.strip()]}
            
            logger.error("✗ No valid response received from Ollama")
            return {"success": False, "error": "Ollama returned invalid response"}
                
        except Exception as e:
            logger.error(f"✗ Error polishing bullets: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def polish_resume(resume_text: str, intensity: str = "medium") -> Dict:
        """
        Polish an entire resume to be stronger and more ATS-optimized.
        
        Args:
            resume_text: Original resume content
            intensity: 'light', 'medium', or 'aggressive'
            
        Returns:
            Dict with success status and polished resume
        """
        try:
            ollama = _get_ollama_service()
            
            # Import the prompt function
            from core.prompts import resume_polish_prompt
            
            prompt = resume_polish_prompt(resume_text, intensity)
            
            logger.info("✨ Polishing resume using Ollama...")
            result = ollama.generate(prompt, stream=False)
            
            if not result.get("success"):
                error_msg = result.get("error", "No response from Ollama. Please try again.")
                logger.error(f"✗ Ollama generation failed: {error_msg}")
                return {"success": False, "error": error_msg}
            
            response = result.get("data", {}).get("response", "").strip()
            
            if not response:
                logger.error("✗ No response text received from Ollama")
                return {"success": False, "error": "No text response from Ollama. Please try again."}
            
            # Validate: Polished resume should contain key sections and reasonable length
            min_length = len(resume_text) * 0.4  # Should be at least 40% of original
            if len(response) < min_length:
                logger.warning(f"⚠️  Polished response significantly shorter: {len(response)} chars vs {len(resume_text)} original")
            
            required_sections = ['experience', 'education', 'skills']
            response_lower = response.lower()
            missing_sections = [s for s in required_sections if s not in response_lower]
            if missing_sections:
                logger.warning(f"⚠️  Polished resume missing sections: {missing_sections}")
            
            logger.info(f"✓ Polished resume: {len(response)} characters")
            return {"success": True, "polished_resume": response}
            
        except Exception as e:
            logger.error(f"✗ Error polishing resume: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def grade_resume(resume_text: str) -> Dict:
        """
        Grade and provide feedback on a resume using Ollama.
        
        Args:
            resume_text: Resume content to grade
            
        Returns:
            Dict with success status and grade data
        """
        try:
            ollama = _get_ollama_service()
            
            prompt = f"""You are an expert recruiter and resume coach. Grade this resume and return ONLY valid JSON with these exact keys:
- score: Overall score (0-100)
- atsScore: ATS compatibility score (0-10)
- sectionsScore: Resume sections and structure score (0-10)
- bulletsScore: Bullet point quality score (0-10)
- contentScore: Content quality and clarity score (0-10)
- keywordsScore: Keyword optimization score (0-10)
- atsFeedback: Brief 1-sentence feedback on ATS compatibility
- strengths: Top 3 strengths (list)
- improvements: Top 3 areas for improvement (list)
- recommendations: Actionable recommendations (list)

RESUME:
{resume_text}

Example format:
{{
  "score": 78,
  "atsScore": 7,
  "sectionsScore": 8,
  "bulletsScore": 6,
  "contentScore": 8,
  "keywordsScore": 7,
  "atsFeedback": "Good ATS compatibility with standard section headers",
  "strengths": ["bullet1", "bullet2", "bullet3"],
  "improvements": ["bullet1", "bullet2", "bullet3"],
  "recommendations": ["item1", "item2", "item3"]
}}"""
            
            logger.info("📊 Grading resume using Ollama...")
            result = ollama.generate(prompt, stream=False)
            
            if not result.get("success"):
                error_msg = result.get("error", "No response from Ollama. Please try again.")
                logger.error(f"✗ Ollama generation failed: {error_msg}")
                return {"success": False, "error": error_msg}
            
            response = result.get("data", {}).get("response", "")
            
            if not response:
                logger.error("✗ No response text received from Ollama")
                return {"success": False, "error": "No text response from Ollama. Please try again."}
            
            # Extract grade data
            grade_data = extract_grade_data(response)
            
            if grade_data:
                logger.info(f"✓ Resume graded: {grade_data.get('score', 0)}/100")
                return {"success": True, "grade": grade_data}
            else:
                logger.error("✗ Failed to parse grade data from response")
                return {"success": False, "error": "Failed to parse resume grading response"}
                
        except Exception as e:
            logger.error(f"✗ Error grading resume: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_changes_summary(original_resume: str, polished_resume: str) -> Dict:
        """
        Generate a summary of specific changes made during polishing.
        
        Args:
            original_resume: Original resume text
            polished_resume: Polished resume text
            
        Returns:
            Dict with success status and list of changes
        """
        try:
            ollama = _get_ollama_service()
            
            from core.prompts import get_changes_summary_prompt
            prompt = get_changes_summary_prompt(original_resume, polished_resume)
            
            logger.info("📊 Generating change summary...")
            result = ollama.generate(prompt, stream=False)
            
            if not result.get("success"):
                logger.warning(f"⚠️  Failed to generate change summary: {result.get('error')}")
                # Return graceful fallback
                return {
                    "success": True,
                    "changes": [
                        "Resume optimized for clarity and impact",
                        "Action verbs strengthened throughout",
                        "Content reorganized for better flow"
                    ]
                }
            
            response = result.get("data", {}).get("response", "").strip()
            
            if not response:
                return {"success": True, "changes": ["Resume enhanced with AI improvements"]}
            
            # Parse JSON array from response
            changes = extract_json_from_response(response)
            
            if isinstance(changes, list) and len(changes) > 0:
                logger.info(f"✓ Generated {len(changes)} change descriptions")
                return {"success": True, "changes": changes}
            else:
                # Fallback if parsing fails
                return {
                    "success": True,
                    "changes": [
                        "Resume optimized for clarity",
                        "Content enhanced with AI suggestions"
                    ]
                }
                
        except Exception as e:
            logger.error(f"✗ Error generating change summary: {e}")
            logger.error(traceback.format_exc())
            # Always return success with fallback changes to not break UX
            return {"success": True, "changes": ["Resume enhanced with AI improvements"]}
    
    @staticmethod
    def parse_to_pdf_format(resume_text: str) -> Dict:
        """
        Parse resume text into structured PDF format.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Dict with success status and parsed resume structure
        """
        try:
            ollama = _get_ollama_service()
            
            from core.prompts import parse_to_pdf_format_prompt
            prompt = parse_to_pdf_format_prompt(resume_text)
            
            logger.info("📄 Parsing resume into structured format using Ollama...")
            result = ollama.generate(prompt, stream=False)
            
            if not result.get("success"):
                error_msg = result.get("error", "No response from Ollama. Please try again.")
                logger.error(f"✗ Ollama generation failed: {error_msg}")
                return {"success": False, "error": error_msg}
            
            response = result.get("data", {}).get("response", "")
            
            if not response:
                logger.error("✗ No response text received from Ollama")
                return {"success": False, "error": "No text response from Ollama. Please try again."}
            
            logger.debug(f"Raw Ollama response: {response[:500]}")
            
            # Parse response and extract structure
            parsed = extract_json_from_response(response)
            
            if parsed and validate_parsed_resume(parsed):
                logger.info("✅ Successfully parsed resume structure from Ollama")
                return {"success": True, "parsed_resume": parsed}
            else:
                logger.error("✗ Parsed data did not match expected resume structure")
                return {"success": False, "error": "Invalid resume structure returned by LLM"}
                
        except Exception as e:
            logger.error(f"✗ Error parsing resume: {e}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
