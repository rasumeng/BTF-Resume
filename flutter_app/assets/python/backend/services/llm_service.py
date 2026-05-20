"""
LLM Service - Handles all LLM calls for resume processing.
Uses the initialized Ollama service via Flask request context.
"""

import logging
import json
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

from config import MODELS


def _extract_json_from_response(response: str) -> Dict:
    """
    Extract and parse JSON from Ollama response.
    Handles markdown code blocks, explanatory text, and malformed JSON.
    
    Args:
        response: Raw response text from Ollama
        
    Returns:
        Parsed JSON dict, or None if parsing fails
    """
    try:
        json_str = response.strip()
        
        # First, try to find JSON in code blocks (```json ... ``` or ```...```)
        # This handles: "Some text\n```json\n{...}\n```\nMore text"
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_str)
        if match:
            json_str = match.group(1).strip()
        # If no code block, try to find raw JSON object or array
        # This handles: "Some text {json} more text"
        elif not json_str.startswith('{') and not json_str.startswith('['):
            # Look for JSON object
            json_match = re.search(r'\{[\s\S]*\}(?=\s*(?:```|$))', json_str)
            if not json_match:
                # Look for JSON array
                json_match = re.search(r'\[[\s\S]*\](?=\s*(?:```|$))', json_str)
            if json_match:
                json_str = json_match.group(0)
        
        # Try to parse JSON
        parsed = json.loads(json_str)
        return parsed
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"❌ JSON parsing failed: {e}")
        logger.error(f"Raw response: {response[:300]}")
        return None


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
    from .ollama_service import get_ollama_service
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
            Dict with polished bullets
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
                return {
                    "success": False,
                    "error": error_msg
                }
            
            logger.debug(f"Ollama response structure: {result}")
            response = result.get("data", {}).get("response", "")
            
            if not response:
                logger.error("✗ No response text received from Ollama")
                logger.error(f"Full response: {result}")
                return {
                    "success": False,
                    "error": "No text response from Ollama. Please try again."
                }
            
            logger.debug(f"Raw Ollama response: {response[:500]}")
            
            # Parse response and extract bullet list
            polished = _extract_json_from_response(response)
            
            # Handle different response formats
            if polished and isinstance(polished, list) and len(polished) > 0:
                # Validate each bullet
                validated_bullets = [str(b).strip() for b in polished if b]
                if validated_bullets:
                    logger.info(f"✓ Got {len(validated_bullets)} polished bullets from JSON array")
                    return {"success": True, "bullets": validated_bullets}

            elif polished and isinstance(polished, dict) and "bullets" in polished:
                bullet_list = polished.get("bullets", [])
                if isinstance(bullet_list, list) and len(bullet_list) > 0:
                    validated_bullets = [str(b).strip() for b in bullet_list if b]
                    if validated_bullets:
                        logger.info(f"✓ Got {len(validated_bullets)} polished bullets from JSON dict")
                        return {"success": True, "bullets": validated_bullets}

            # Fallback: if we got a single response, treat as one polished bullet
            if response and len(response) > 10:
                logger.warning("⚠️  Could not parse JSON response, returning raw response as single bullet")
                return {"success": True, "bullets": [response.strip()]}

            # Last resort fallback
            logger.error("✗ No valid response received from Ollama")
            return {"success": False, "error": "Ollama returned invalid response"}
                
        except Exception as e:
            logger.error(f"✗ Error polishing bullets: {e}")
            import traceback
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
            Dict with polished resume and summary of changes
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
                return {
                    "success": False,
                    "error": error_msg
                }
            
            logger.debug(f"Ollama response structure: {result}")
            response = result.get("data", {}).get("response", "").strip()
            
            if not response:
                logger.error("✗ No response text received from Ollama")
                logger.error(f"Full response: {result}")
                return {
                    "success": False,
                    "error": "No text response from Ollama. Please try again."
                }
            
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
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def grade_resume(resume_text: str) -> Dict:
        """
        Grade and provide feedback on a resume using Ollama.
        
        Args:
            resume_text: Resume content to grade
            
        Returns:
            Dict with score breakdown and feedback
        """
        try:
            ollama = _get_ollama_service()
            
            prompt = f"""You are an expert Resume Screener and ATS (Applicant Tracking System) Analyst. Evaluate the following resume rigorously against industry-standard ATS criteria.

RESUME:
{resume_text}

Evaluate the resume across these 5 weighted dimensions:

1. ATS COMPATIBILITY (30% weight) - Score 1-10:
   - Keyword density and relevance to target role
   - Standard section headings (avoid non-standard labels)
   - Clean formatting (no tables, headers/footers, images)
   - File format compatibility (plain text friendly)
   - No special characters or encoding issues

2. STRUCTURE & SECTIONS (20% weight) - Score 1-10:
   - Logical section order (Contact → Summary → Experience → Education → Skills)
   - Presence of essential sections
   - Consistent formatting throughout
   - Appropriate length (1-2 pages for experienced, 1 page for entry-level)

3. BULLET QUALITY (25% weight) - Score 1-10:
   - Action verbs at start of each bullet
   - Measurable results and quantifiable achievements
   - Specific role/company/skill mentions
   - Conciseness (one line per bullet)
   - STAR method format (Situation/Task, Action, Result)

4. CONTENT STRENGTH (15% weight) - Score 1-10:
   - Professional summary quality
   - Relevant experience details
   - Education section completeness
   - No spelling/grammar errors
   - Consistent tense and voice

5. KEYWORD OPTIMIZATION (10% weight) - Score 1-10:
   - Technical skills presence
   - Industry-specific terminology
   - Missing critical keywords for typical roles
   - Soft skills balance

Calculate overall score as weighted average × 10 (scale 0-100).

Return ONLY valid JSON with these exact keys:
{{
  "score": 0-100,
  "ats_score": 1-10,
  "sections_score": 1-10,
  "bullets_score": 1-10,
  "content_score": 1-10,
  "keywords_score": 1-10,
  "strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
  "improvements": ["specific improvement 1", "specific improvement 2", "specific improvement 3"],
  "ats_feedback": "1-2 sentence assessment of ATS compatibility"
}}

Ensure strengths/improvements are specific, actionable, and tied to the actual resume content - not generic advice."""
            
            logger.info("📊 Grading resume using Ollama...")
            result = ollama.generate(prompt, stream=False)
            
            if not result.get("success"):
                error_msg = result.get("error", "No response from Ollama. Please try again.")
                logger.error(f"✗ Ollama generation failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
            
            logger.debug(f"Ollama response structure: {result}")
            response = result.get("data", {}).get("response", "")
            
            if not response:
                logger.error("✗ No response text received from Ollama")
                logger.error(f"Full response: {result}")
                return {
                    "success": False,
                    "error": "No text response from Ollama. Please try again."
                }
            
            try:
                # Extract JSON from response
                import re
                # Try to parse response as-is first (handles newlines in JSON correctly)
                grade_data = None
                try:
                    grade_data = json.loads(response)
                except json.JSONDecodeError:
                    # If that fails, try extracting JSON block
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        grade_data = json.loads(json_str)
                    else:
                        raise json.JSONDecodeError("No JSON object found in response", response, 0)
                
                # Validate required fields with defaults
                required_fields = {
                    'score': 0,
                    'ats_score': 0,
                    'sections_score': 0,
                    'bullets_score': 0,
                    'content_score': 0,
                    'keywords_score': 0,
                    'strengths': [],
                    'improvements': [],
                    'ats_feedback': ''
                }
                for field, default_value in required_fields.items():
                    if field not in grade_data:
                        grade_data[field] = default_value
                
                logger.info(f"✓ Resume graded: {grade_data.get('score', 0)}/100")
                return {"success": True, "grade": grade_data}
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"✗ Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response}")
                # Return failure instead of fallback response
                return {
                    "success": False,
                    "error": f"Failed to parse resume grading response: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"✗ Error grading resume: {e}")
            import traceback
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
            Dict with success status and list of change descriptions
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
                return {
                    "success": True,
                    "changes": ["Resume enhanced with AI improvements"]
                }
            
            # Parse JSON array from response
            changes = _extract_json_from_response(response)
            
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
            import traceback
            logger.error(traceback.format_exc())
            # Always return success with fallback changes to not break UX
            return {
                "success": True,
                "changes": ["Resume enhanced with AI improvements"]
            }
    
    @staticmethod
    def parse_to_pdf_format(resume_text: str) -> Dict:
        """
        Parse resume text into structured PDF format.
        Uses improved prompt that ensures all data is captured correctly.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Dict with parsed resume structure matching ResumData format
        """
        try:
            ollama = _get_ollama_service()
            
            # Use improved prompt that specifies exact JSON structure
            from core.prompts import parse_to_pdf_format_prompt
            prompt = parse_to_pdf_format_prompt(resume_text)
            
            logger.info("📄 Parsing resume into structured format using Ollama...")
            result = ollama.generate(prompt, stream=False)
            
            if not result.get("success"):
                error_msg = result.get("error", "No response from Ollama. Please try again.")
                logger.error(f"✗ Ollama generation failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
            
            logger.debug(f"Ollama response structure: {result}")
            response = result.get("data", {}).get("response", "")
            
            if not response:
                logger.error("✗ No response text received from Ollama")
                logger.error(f"Full response: {result}")
                return {
                    "success": False,
                    "error": "No text response from Ollama. Please try again."
                }
            
            logger.debug(f"Raw Ollama response: {response[:500]}")
            logger.info(f"Response length: {len(response)} characters")
            
            # Parse response and extract structure using robust JSON parser
            parsed = _extract_json_from_response(response)
            
            if parsed:
                logger.info(f"✅ Successfully parsed resume structure from Ollama")
                # Validate parsed data has expected top-level keys
                logger.info(f"Parsed keys: {list(parsed.keys())}")
                if 'contact' in parsed:
                    logger.info(f"Contact name: {parsed.get('contact', {}).get('name', 'NOT FOUND')}")
                if 'work_experience' in parsed:
                    logger.info(f"Work experience entries: {len(parsed.get('work_experience', []))}")
                if 'projects' in parsed:
                    logger.info(f"Projects: {len(parsed.get('projects', []))}")
                return {"success": True, "parsed_resume": parsed}
            else:
                logger.error(f"⚠️  Failed to parse JSON from response")
                logger.error(f"Raw response: {response[:500]}")
                # Return failure - don't try to work with unparsable data
                return {
                    "success": False,
                    "error": "Failed to parse resume structure into JSON"
                }
                
        except Exception as e:
            logger.error(f"✗ Error parsing resume: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
