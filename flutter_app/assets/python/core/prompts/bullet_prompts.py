"""
Bullet-point level prompts for polishing and generating individual resume bullets.
"""


def bullet_polish_prompt(bullet: str, mode: str = "medium") -> str:
    """
    Generate a prompt to polish a single resume bullet point.
    
    Args:
        bullet: The bullet point text to polish
        mode: Intensity level - 'light', 'medium', or 'aggressive'
        
    Returns:
        Complete prompt for LLM
    """
    mode_instructions = {
        "light": (
            "Make minimal changes. Only fix weak or vague verbs and tighten wording. "
            "Preserve the original structure and content as closely as possible."
        ),
        "medium": (
            "Improve clarity, verb precision, and impact. You may restructure the bullet "
            "if it improves readability, but do not change the substance of what was done."
        ),
        "aggressive": (
            "Fully rewrite for maximum impact. Restructure freely, sharpen the verb, "
            "and make the accomplishment as compelling as possible without inventing experience."
        ),
    }

    return f"""You are a professional resume editor. Rewrite the following resume bullet point.

BULLET:
{bullet}

REWRITE RULES:
1. Begin with a precise action verb that reflects the specific nature of the work in this bullet.
   - Choose the verb based on what was actually done, not from a fixed list.
   - If the original verb is already specific and accurate, keep it.
   - Only replace verbs that are weak, vague, or generic (e.g. "helped", "worked on", "assisted", "did", "was responsible for").
2. Follow the structure: [Action Verb] + [What was done] + [Tools/Technologies used] + [Outcome or impact].
3. Preserve every technology, tool, and language mentioned in the original — do not drop any.
4. If a measurable result is present, keep it. If one is strongly implied and you can represent it with a natural placeholder like [X%] or [N users], you may add it. If no metric fits naturally, omit it entirely. NEVER write [N/A], [none], or any explanatory bracket text.
5. Do NOT add skills, tools, or experience that are not in the original bullet.
6. Maximum 180 characters.
7. Do NOT include a leading "- " prefix.
8. Return only the rewritten bullet. No explanation, no commentary, no alternatives.

INTENSITY: {mode_instructions[mode]}

REWRITTEN BULLET:"""


def experience_updater_prompt(user_input: str) -> str:
    """
    Generate a prompt to convert experience description into resume bullets.
    
    Args:
        user_input: User's description of their experience
        
    Returns:
        Complete prompt for LLM to generate 2-4 bullet points
    """
    return f"""You are a professional resume writer. Convert the following experience description into 2-4 resume bullet points.

EXPERIENCE DESCRIPTION:
{user_input}

RULES:
1. Extract 2-4 distinct accomplishments or responsibilities from the description.
2. Each bullet must begin with a precise action verb that matches what was actually done in that specific task.
   - Derive the verb from the nature of the work — do not default to the same verb across bullets.
   - Avoid weak or overused openers like "Developed", "Worked on", "Helped", or "Was responsible for".
3. Follow the structure: [Action Verb] + [What was done] + [Tools/Technologies] + [Result or impact].
4. If a metric is stated, include it. If one is implied, use a placeholder like [X%] or [N users].
5. Maximum 180 characters per bullet.
6. Each bullet must start with "- ".
7. Return only the bullets. No explanation, no preamble.

BULLETS:"""
