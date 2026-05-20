"""
Resume grading and evaluation prompts.
"""


def get_grader_prompt(resume_text: str) -> str:
    """
    Generate a prompt to grade a resume across multiple dimensions.
    
    Args:
        resume_text: Resume text to grade
        
    Returns:
        Complete prompt for LLM to return scoring JSON
    """
    return f"""You are a professional resume reviewer. Grade the following resume across 4 dimensions.

RESUME:
{resume_text}

Score each dimension from 1 to 10 using these criteria:
- ats_score: How well the resume would pass Applicant Tracking Systems (keywords, formatting, standard sections)
- sections_score: Whether the resume has the right sections (Education, Experience, Projects, Skills) and organizes them clearly
- bullets_score: Quality of bullet points — action verbs, measurable results, specificity, conciseness
- keywords_score: Presence of relevant technical and industry keywords for the apparent target role

Return ONLY a valid JSON object in exactly this format, with no explanation, no preamble, no markdown:
{{"ats_score": 0, "sections_score": 0, "bullets_score": 0, "keywords_score": 0}}

SCORES:"""
