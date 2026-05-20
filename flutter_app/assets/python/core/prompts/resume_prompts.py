"""
Resume-level prompts for polishing entire resumes and generating summaries of changes.
"""


def resume_polish_prompt(resume_text: str, mode: str = "medium") -> str:
    """
    Generate a prompt to polish an entire resume.
    
    Args:
        resume_text: Complete resume text to polish
        mode: Intensity level - 'light', 'medium', or 'aggressive'
        
    Returns:
        Complete prompt for LLM
    """
    mode_instructions = {
        "light": (
            "Make minimal changes. Fix weak verbs, tighten wording, and improve clarity. "
            "Preserve the original structure and content."
        ),
        "medium": (
            "Improve clarity, verb precision, and overall impact. You may restructure sections "
            "and improve phrasing, but preserve all original accomplishments and content."
        ),
        "aggressive": (
            "Fully optimize for impact and clarity. Sharpen every verb, restructure for better flow, "
            "and make all accomplishments maximally compelling without inventing experience."
        ),
    }

    return f"""You are enhancing an existing resume. Your job is to improve the writing, clarity, and impact of a resume that has ALREADY BEEN WRITTEN BY THE USER based on their real experience.

READ THIS CAREFULLY:
- You are NOT creating or writing a new resume from scratch
- You are NOT inventing any experience or accomplishments
- You are ONLY editing and improving the resume text that is provided below
- All experience described is real and verified by the user
- Your job is to make it more polished, clear, and impactful

Here is the existing resume to enhance:

RESUME:
{resume_text}

ENHANCEMENT RULES:
1. For each bullet point, use a precise action verb that reflects what was actually done.
   - Only replace weak or generic verbs (e.g. "helped", "worked on", "assisted", "did", "was responsible for").
   - Keep strong, specific verbs that accurately describe the work.
   - Do not reuse the same verb across multiple consecutive bullets.
2. Improve clarity, conciseness, and impact of all content.
3. Preserve every technology, tool, skill, accomplishment, and measurable result from the original.
4. Maintain proper structure: Keep section headings, organization, dates, company names, all as they are.
5. Do NOT add ANY skills, tools, or experience that are not already in the original resume.
6. Keep bullet points to 180 characters maximum.
7. Return the complete enhanced resume in the same structure as the original.
8. Do NOT explain your changes - just provide the improved resume.

INTENSITY LEVEL: {mode_instructions[mode]}

ENHANCED RESUME (same structure, improved writing):"""


def get_changes_summary_prompt(original: str, polished: str) -> str:
    """
    Generate a prompt to identify and summarize changes between original and polished resume.
    
    Args:
        original: The original resume text
        polished: The polished resume text
        
    Returns:
        Complete prompt for LLM
    """
    return f"""You are comparing an original resume with an enhanced version.

Identify 5-8 specific meaningful changes organized by resume section.

For each change, use this format: "In [Section]: Changed 'X' -> 'Y'" or "In [Section]: Changed X to Y"

Resume Sections: Work Experience, Education, Skills, Projects, Summary, Certifications, Leadership, Other

Examples of good descriptions:
- "In Work Experience: Changed 'Managed team' -> 'Led cross-functional team of 8 people'"
- "In Skills: Restructured bullet to highlight technical expertise first"
- "In Summary: Added quantifiable achievements and impact metrics"
- "In Projects: Changed passive 'was developed' -> active 'architected and deployed'"
- "In Work Experience: Tightened description, removing vague language"

Requirements:
- Format: "In [Section]: Changed X -> Y" or "In [Section]: [specific improvement]"
- Identify which resume section was affected
- Show specific before/after when possible
- Focus on meaningful improvements only
- Maximum 8 changes total
- Return ONLY valid JSON array format: ["In Section: change 1", "In Section: change 2"]

If no significant changes in a section, don't mention it.

Original Resume:
{original}

Enhanced Resume:
{polished}

Return ONLY the JSON array (no other text):""".strip()
