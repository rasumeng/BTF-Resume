"""
Job tailoring prompts for matching resumes to specific job descriptions.
"""


def job_tailor_prompt(resume_section: str, job_description: str, intensity: str = "medium") -> str:
    """
    Generate a prompt to rewrite resume bullets to align with a job description.
    
    Args:
        resume_section: Resume bullets to tailor
        job_description: Target job description
        intensity: Tailoring aggressiveness
        
    Returns:
        Complete prompt for LLM
    """
    intensity_instructions = {
        "light": (
            "Make minimal changes. Only reframe bullets to naturally incorporate relevant keywords. "
            "Keep 90% of original wording."
        ),
        "medium": (
            "Reorder and reframe content to highlight relevant skills and experience. "
            "Keep 80% of original content. Naturally incorporate job description keywords."
        ),
        "heavy": (
            "Extensively reframe all content to maximize relevance. Can rewrite bullets completely "
            "to emphasize transferable skills. Keep core facts but shift framing."
        ),
    }

    base_prompt = f"""You are a professional resume editor. Rewrite the following resume bullets to better align with the job description.

RESUME BULLETS:
{resume_section}

JOB DESCRIPTION:
{job_description}

RULES:
1. Return exactly the same number of bullets as provided — no more, no fewer.
2. Each bullet must begin with a precise action verb that reflects what was actually done in that bullet.
   - If the original verb is already accurate and strong, keep it.
   - Only replace verbs that are weak or generic.
   - Do not reuse the same verb across multiple bullets.
3. Incorporate relevant keywords and terminology from the job description naturally — do not force them in awkwardly.
4. Preserve the original accomplishments exactly. Do not swap in responsibilities copied from the job posting.
5. Do NOT add any skills, tools, or technologies that are not present in the original bullets.
6. Maximum 180 characters per bullet.
7. Do NOT include a leading "- " prefix.
8. Return only the rewritten bullets, one per line. No explanation or commentary.

REWRITTEN BULLETS:"""

    return base_prompt + f"\n\nTAILORING INTENSITY: {intensity_instructions.get(intensity, intensity_instructions['medium'])}"
