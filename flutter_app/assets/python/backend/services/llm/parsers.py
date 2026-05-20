"""
JSON response parsers - Handles extraction and parsing of structured data from LLM responses.
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def _extract_balanced_json_block(text: str) -> Optional[str]:
    """Extract the first balanced JSON object/array from free-form text."""
    if not text:
        return None

    start_idx = None
    start_char = None

    for i, ch in enumerate(text):
        if ch in "[{":
            start_idx = i
            start_char = ch
            break

    if start_idx is None:
        return None

    stack = []
    in_string = False
    escaped = False

    for i in range(start_idx, len(text)):
        ch = text[i]

        if in_string:
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch in "[{":
            stack.append(ch)
            continue

        if ch in "]}":
            if not stack:
                continue
            opener = stack.pop()
            if (opener == "{" and ch != "}") or (opener == "[" and ch != "]"):
                return None
            if not stack:
                return text[start_idx : i + 1]

    # If the model truncated output, close open brackets heuristically.
    if stack:
        snippet = text[start_idx:]
        closing = ""
        for opener in reversed(stack):
            closing += "}" if opener == "{" else "]"
        return snippet + closing

    return None


def _repair_common_json_issues(json_str: str) -> str:
    """Apply safe repairs for common LLM JSON formatting mistakes."""
    if not json_str:
        return json_str

    repaired = json_str.strip()

    # Remove trailing commas before object/array close.
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    # Remove control chars except tab/newline/carriage return.
    repaired = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", repaired)

    return repaired


def _normalize_resume_shape(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize key aliases and ensure expected top-level sections exist."""
    if not isinstance(parsed, dict):
        return parsed

    alias_map = {
        "workExperience": "work_experience",
        "work history": "work_experience",
        "experience": "work_experience",
        "project": "projects",
        "education_history": "education",
    }

    normalized = dict(parsed)
    for src, target in alias_map.items():
        if src in normalized and target not in normalized:
            normalized[target] = normalized[src]

    if "contact" not in normalized or not isinstance(normalized.get("contact"), dict):
        normalized["contact"] = normalized.get("contact") if isinstance(normalized.get("contact"), dict) else {}

    for key in ["work_experience", "projects", "education", "leadership", "skills"]:
        value = normalized.get(key, [])
        if isinstance(value, dict):
            normalized[key] = [value]
        elif isinstance(value, list):
            normalized[key] = value
        else:
            normalized[key] = []

    return normalized


def extract_json_from_response(response: str) -> Optional[Dict]:
    """
    Extract and parse JSON from Ollama response.
    Handles markdown code blocks, explanatory text, and malformed JSON.
    
    Args:
        response: Raw response text from Ollama
        
    Returns:
        Parsed JSON dict/list, or None if parsing fails
    """
    json_candidate = (response or "").strip()

    # 1) Extract from fenced code block if present.
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_candidate)
    if match:
        json_candidate = match.group(1).strip()

    # 2) Extract balanced JSON block from free text.
    extracted = _extract_balanced_json_block(json_candidate)
    if extracted:
        json_candidate = extracted

    # 3) Try parse raw, then repaired JSON.
    for candidate in [json_candidate, _repair_common_json_issues(json_candidate)]:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return _normalize_resume_shape(parsed)
            return parsed
        except (json.JSONDecodeError, TypeError):
            continue

    logger.error("❌ JSON parsing failed after recovery attempts")
    logger.error(f"Raw response: {response[:300]}")
    return None


def validate_parsed_resume(parsed: Dict) -> bool:
    """
    Validate that parsed resume has expected structure.
    
    Args:
        parsed: Parsed resume dictionary
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(parsed, dict):
        return False
    
    if "contact" not in parsed:
        return False

    # Accept resumes even when one optional section is missing.
    has_any_section = bool(
        parsed.get("work_experience")
        or parsed.get("projects")
        or parsed.get("education")
        or parsed.get("leadership")
        or parsed.get("skills")
        or parsed.get("summary")
    )
    return has_any_section


def extract_bullet_list(response: str) -> Optional[List[str]]:
    """
    Extract bullet points from LLM response.
    
    Args:
        response: Raw response from LLM
        
    Returns:
        List of bullet points, or None if parsing fails
    """
    parsed = extract_json_from_response(response)
    
    if parsed is None:
        return None
    
    # Handle different response formats
    if isinstance(parsed, list):
        return [str(b).strip() for b in parsed if b]
    
    if isinstance(parsed, dict):
        if "bullets" in parsed:
            bullet_list = parsed.get("bullets", [])
            if isinstance(bullet_list, list):
                return [str(b).strip() for b in bullet_list if b]
    
    return None


def extract_grade_data(response: str) -> Optional[Dict]:
    """
    Extract grade data from LLM response.
    
    Args:
        response: Raw response from LLM
        
    Returns:
        Grade data dictionary with score, strengths, improvements, recommendations
    """
    try:
        # Try to parse response as-is first
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
        
        # Validate required fields
        required_fields = [
            'score', 'atsScore', 'sectionsScore', 'bulletsScore',
            'contentScore', 'keywordsScore', 'atsFeedback',
            'strengths', 'improvements', 'recommendations'
        ]
        for field in required_fields:
            if field not in grade_data:
                if field in ['atsScore', 'sectionsScore', 'bulletsScore', 'contentScore', 'keywordsScore']:
                    grade_data[field] = 0
                elif field == 'atsFeedback':
                    grade_data[field] = ''
                elif field == 'score':
                    grade_data[field] = 0
                else:
                    grade_data[field] = []
        
        return grade_data
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"❌ Failed to parse grade data: {e}")
        return None
