"""
Job Tailor Service - Enhanced tailoring with confidence scoring, gap analysis, and category breakdowns.
"""

import logging
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

from services.llm import LLMService
from core.prompts import job_tailor_prompt


@dataclass
class TailorMatch:
    """Represents a single match between resume and job"""
    category: str  # 'Skills' | 'Experience' | 'Keywords'
    keyword: str
    relevance: int  # 0-100
    source: str  # e.g., "Software Engineer role" or "Technical Skills section"


@dataclass
class CategoryScore:
    """Score breakdown by category"""
    category: str  # 'Skills' | 'Experience' | 'Keywords'
    score: int  # 0-100


@dataclass
class GapAnalysis:
    """Missing skills/keywords not in resume"""
    missing_skills: List[str]
    missing_keywords: List[str]
    suggestions: List[str]  # AI-generated bullet suggestions


@dataclass
class JobTailorResult:
    """Complete tailor result with all enhancements"""
    overall_confidence: int  # 0-100
    category_scores: List[CategoryScore]
    matches: List[TailorMatch]
    gaps: GapAnalysis
    tailored_resume_text: str  # The modified resume text
    changes_summary: str  # Brief description of what changed


class JobTailorService:
    """Service for intelligent job tailoring with detailed analysis."""

    @staticmethod
    def tailor_resume(
        resume_text: str,
        job_description: str,
        intensity: str = "medium"  # 'light' | 'medium' | 'heavy'
    ) -> Optional[JobTailorResult]:
        """
        Tailor resume to job description with comprehensive analysis.
        
        Args:
            resume_text: The original resume content
            job_description: The job description to tailor for
            intensity: How aggressively to modify ('light', 'medium', 'heavy')
            
        Returns:
            JobTailorResult with all analysis data, or None if it fails
        """
        try:
            # Step 1: Extract job requirements
            job_requirements = JobTailorService._extract_job_requirements(job_description)
            
            # Step 2: Analyze resume vs job
            matches = JobTailorService._find_matches(resume_text, job_requirements)
            
            # Step 3: Identify gaps
            gaps = JobTailorService._identify_gaps(resume_text, job_requirements, matches)
            
            # Step 4: Calculate scores
            category_scores = JobTailorService._calculate_category_scores(matches)
            overall_confidence = JobTailorService._calculate_overall_confidence(category_scores)
            
            # Step 5: Tailor the resume
            tailored_text, changes = JobTailorService._apply_tailoring(
                resume_text,
                job_requirements,
                matches,
                intensity
            )
            
            return JobTailorResult(
                overall_confidence=overall_confidence,
                category_scores=category_scores,
                matches=matches,
                gaps=gaps,
                tailored_resume_text=tailored_text,
                changes_summary=changes
            )
            
        except Exception as e:
            logger.error(f"Error in tailor_resume: {e}")
            return None

    @staticmethod
    def _extract_job_requirements(job_description: str) -> Dict:
        """Extract structured requirements from job description using LLM."""
        try:
            prompt = f"""Analyze this job description and extract structured requirements.
            
Job Description:
{job_description}

Return JSON with exactly these fields (use empty arrays if not found):
{{
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill3", "skill4"],
    "experience_level": "senior|mid|junior|entry",
    "key_responsibilities": ["resp1", "resp2"],
    "role_title": "The job title",
    "company_context": "Brief context about the role"
}}

Return ONLY valid JSON, no markdown."""
            
            result = LLMService.call_ollama(prompt)
            if result:
                try:
                    import json
                    # Handle case where result is already a dict
                    if isinstance(result, dict):
                        return result
                    # Try to parse JSON string
                    parsed = json.loads(result)
                    logger.info(f"✓ Extracted job requirements: {len(parsed.get('required_skills', []))} required skills")
                    return parsed
                except (json.JSONDecodeError, ValueError):
                    logger.warning("⚠️  Could not parse job requirements JSON, using defaults")
                    return {"required_skills": [], "preferred_skills": [], "key_responsibilities": [], "role_title": "Position"}
            return {"required_skills": [], "preferred_skills": [], "key_responsibilities": []}
            
        except Exception as e:
            logger.error(f"Error extracting job requirements: {e}")
            return {"required_skills": [], "preferred_skills": [], "key_responsibilities": []}

    @staticmethod
    def _find_matches(resume_text: str, job_requirements: Dict) -> List[TailorMatch]:
        """Find matches between resume and job requirements using LLM for accuracy."""
        matches = []
        try:
            required_skills = job_requirements.get("required_skills", [])
            key_responsibilities = job_requirements.get("key_responsibilities", [])
            
            if not required_skills and not key_responsibilities:
                logger.warning("⚠️  No job requirements to match against")
                return []
            
            # Build analysis prompt
            prompt = f"""Analyze how well this resume matches these job requirements. For each requirement, identify how it appears in the resume with a relevance score (0-100).

RESUME:
{resume_text[:2000]}  {chr(10)}

REQUIRED SKILLS: {', '.join(required_skills[:7])}
KEY RESPONSIBILITIES: {', '.join(key_responsibilities[:5])}

Find matches in these categories:
- Skills: Technical or professional skills mentioned
- Experience: Job titles, roles, or responsibilities done
- Projects: Projects, tools, or initiatives worked on
- Keywords: Industry terms, frameworks, or soft skills

Return JSON array with this exact format (max 10 matches, prioritize all categories):
[
    {{"category": "Skills", "keyword": "skill_name", "relevance": 85, "source": "where it's mentioned"}},
    {{"category": "Experience", "keyword": "responsibility", "relevance": 90, "source": "context"}},
    {{"category": "Projects", "keyword": "project_name", "relevance": 80, "source": "section"}},
    {{"category": "Keywords", "keyword": "key_term", "relevance": 80, "source": "section"}}
]

Return ONLY valid JSON array, no markdown or explanations."""
            
            result = LLMService.call_ollama(prompt)
            if result:
                try:
                    import json
                    # Parse JSON
                    if isinstance(result, str):
                        matches_data = json.loads(result)
                    else:
                        matches_data = result
                    
                    # Convert to TailorMatch objects
                    for match_dict in matches_data[:10]:  # Limit to 10 matches
                        try:
                            matches.append(TailorMatch(
                                category=match_dict.get("category", "Keywords"),
                                keyword=match_dict.get("keyword", ""),
                                relevance=int(match_dict.get("relevance", 75)),
                                source=match_dict.get("source", "Resume content")
                            ))
                        except (KeyError, ValueError, TypeError):
                            logger.warning(f"⚠️  Could not parse match: {match_dict}")
                            continue
                    
                    logger.info(f"✓ Found {len(matches)} matches using LLM analysis (including projects)")
                    return matches
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"⚠️  Could not parse LLM matches: {e}")
                    return []
            
            return []
            
        except Exception as e:
            logger.error(f"Error finding matches: {e}")
            return []

    @staticmethod
    def _identify_gaps(
        resume_text: str,
        job_requirements: Dict,
        matches: List[TailorMatch]
    ) -> GapAnalysis:
        """Identify skills and keywords missing from resume using LLM."""
        try:
            required_skills = job_requirements.get("required_skills", [])
            matched_skills = {m.keyword.lower() for m in matches if m.category == "Skills"}
            
            missing_skills = [
                skill for skill in required_skills
                if skill.lower() not in matched_skills and skill.lower() not in resume_text.lower()
            ][:3]  # Top 3 missing

            prompt = f"""Analyze this resume against the job requirements to identify gaps.
RESUME:
{resume_text[:2500]}
REQUIRED SKILLS (already analyzed): {', '.join(required_skills[:10])}
ALREADY MATCHED: {', '.join([m.keyword for m in matches])}
Return ONLY valid JSON with this exact structure:
{{
    "missing_keywords": ["top 3-5 important terms from job description not clearly present in resume"],
    "suggestions": ["specific actionable suggestion 1", "specific actionable suggestion 2", "specific actionable suggestion 3"]
}}
Rules:
- missing_keywords: industry terms, tools, frameworks from the job that are not well-represented in the resume
- suggestions: concrete, specific ways to address gaps using EXISTING experience — do not invent new skills
- Return ONLY valid JSON, no markdown, no explanation."""
            result = LLMService.call_ollama(prompt)
            if result:
                try:
                    parsed = json.loads(result)
                    return GapAnalysis(
                        missing_skills=missing_skills,
                        missing_keywords=parsed.get("missing_keywords", [])[:3],
                        suggestions=parsed.get("suggestions", [])[:3]
                    )
                except (json.JSONDecodeError, KeyError):
                    logger.warning("⚠️  Could not parse gap analysis JSON")
            
            return GapAnalysis(
                missing_skills=missing_skills,
                missing_keywords=[],
                suggestions=["Add specific metrics to quantify your achievements", "Emphasize cross-functional collaboration", "Highlight process improvements"]
            )
            
        except Exception as e:
            logger.error(f"Error identifying gaps: {e}")
            return GapAnalysis(missing_skills=[], missing_keywords=[], suggestions=[])

    @staticmethod
    def _calculate_category_scores(matches: List[TailorMatch]) -> List[CategoryScore]:
        """Calculate average score per category."""
        categories = {}
        for match in matches:
            if match.category not in categories:
                categories[match.category] = []
            categories[match.category].append(match.relevance)
        
        scores = []
        for category, relevances in categories.items():
            avg_score = sum(relevances) // len(relevances) if relevances else 0
            scores.append(CategoryScore(category=category, score=avg_score))
        
        return scores

    @staticmethod
    def _calculate_overall_confidence(category_scores: List[CategoryScore]) -> int:
        """Calculate overall confidence from category scores."""
        if not category_scores:
            return 0
        total = sum(cs.score for cs in category_scores)
        return total // len(category_scores)

    @staticmethod
    def _apply_tailoring(
        resume_text: str,
        job_requirements: Dict,
        matches: List[TailorMatch],
        intensity: str
    ) -> tuple:
        """Apply tailoring modifications to resume using LLM based on intensity."""
        try:
            required_skills = job_requirements.get("required_skills", [])
            key_responsibilities = job_requirements.get("key_responsibilities", [])
            role_title = job_requirements.get("role_title", "Position")

            combined_job = f"""Position: {role_title}
Required Skills: {', '.join(required_skills[:5])}
Key Responsibilities: {'; '.join(key_responsibilities[:5])}"""

            prompt = job_tailor_prompt(
                resume_section=resume_text,
                job_description=combined_job,
                intensity=intensity
            )
            
            # Call LLM to generate tailored resume
            result = LLMService.call_ollama(prompt)
            if result:
                changes = f"Resume tailored with {intensity} intensity to match {role_title} requirements"
                return result, changes
            else:
                logger.warning("⚠️  LLM tailoring failed, returning original")
                changes = f"Resume tailoring attempted with {intensity} intensity"
                return resume_text, changes
                
        except Exception as e:
            logger.error(f"Error applying tailoring: {e}")
            return resume_text, f"Tailoring incomplete: {str(e)}"


# For mock/testing purposes - generates sample result
def generate_sample_tailor_result() -> JobTailorResult:
    """Generate sample tailor result for UI testing."""
    return JobTailorResult(
        overall_confidence=87,
        category_scores=[
            CategoryScore(category="Skills", score=92),
            CategoryScore(category="Experience", score=88),
            CategoryScore(category="Keywords", score=85),
        ],
        matches=[
            TailorMatch(category="Skills", keyword="Project Management", relevance=92, source="Current role"),
            TailorMatch(category="Skills", keyword="Agile/Scrum", relevance=88, source="Work experience"),
            TailorMatch(category="Experience", keyword="Cross-functional team leadership", relevance=95, source="Team lead role"),
            TailorMatch(category="Experience", keyword="Budget management", relevance=87, source="PM responsibilities"),
            TailorMatch(category="Keywords", keyword="Data-driven decision making", relevance=91, source="Resume summary"),
            TailorMatch(category="Keywords", keyword="Stakeholder communication", relevance=85, source="Work bullets"),
        ],
        gaps=GapAnalysis(
            missing_skills=["Advanced SQL", "Tableau", "Statistical Analysis"],
            missing_keywords=["Salesforce", "HubSpot"],
            suggestions=[
                "Highlight your experience with cross-functional teams",
                "Quantify your budget management scale (e.g., $2M+ budget)",
                "Add specific examples of data-driven decisions"
            ]
        ),
        tailored_resume_text="[Tailored resume content would go here]",
        changes_summary="Reordered bullets to emphasize project management and analytics skills. Added context for leadership experience."
    )
