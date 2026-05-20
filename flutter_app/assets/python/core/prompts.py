"""
DEPRECATED: This module is maintained for backward compatibility.
Please import from core.prompts package instead.

Example:
    from core.prompts import bullet_polish_prompt, resume_polish_prompt
"""

import warnings

warnings.warn(
    "Importing from core.prompts as a module is deprecated. "
    "Please use from core.prompts import instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all prompt functions from the new package structure
from prompts import (
    bullet_polish_prompt,
    experience_updater_prompt,
    resume_polish_prompt,
    get_changes_summary_prompt,
    job_tailor_prompt,
    get_grader_prompt,
    parse_resume_structure_prompt,
    parse_to_pdf_format_prompt,
    parse_resume_to_pdf_format_prompt,
)

__all__ = [
    "bullet_polish_prompt",
    "experience_updater_prompt",
    "resume_polish_prompt",
    "get_changes_summary_prompt",
    "job_tailor_prompt",
    "get_grader_prompt",
    "parse_resume_structure_prompt",
    "parse_to_pdf_format_prompt",
    "parse_resume_to_pdf_format_prompt",
]
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


def parse_to_pdf_format_prompt(resume_text: str) -> str:
    """Generate a prompt to parse resume text into structured JSON for PDF generation
    
    The JSON output must match the ResumData structure exactly for proper PDF generation.
    """
    return f"""Parse this resume text and structure it for PDF generation.
Extract ALL information and organize into the exact JSON format specified below.

CRITICAL REQUIREMENTS:
1. Extract the COMPLETE name from contact info - this MUST be set correctly
2. Do NOT use placeholder names like "Resume" or "John Doe" unless that's the actual name
3. Include ALL work experience - do not skip or summarize
4. Include ALL projects with full descriptions
5. Include ALL education entries
6. Include ALL leadership/activities roles
7. Preserve all skills and certifications
8. For each bullet point, extract the COMPLETE text - no truncation
9. Return ONLY valid JSON - no markdown, code blocks, or explanations

RESUME TEXT TO PARSE:
{resume_text}

Return ONLY valid JSON matching this exact structure:
{{
  "contact": {{
    "name": "FULL NAME HERE",
    "email": "email@example.com",
    "phone": "phone number",
    "location": "city, state",
    "linkedin": "linkedin url",
    "github": "github url"
  }},
  "summary": "Professional summary if present",
  "work_experience": [
    {{
      "position": "Job Title",
      "company": "Company Name",
      "start_date": "Start Date",
      "end_date": "End Date",
      "location": "Location if available",
      "bullets": ["Full bullet text 1", "Full bullet text 2"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "date": "Project Date",
      "technologies": "Tech stack",
      "location": "Location if applicable",
      "bullets": ["Full project bullet 1", "Full project bullet 2"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree Type",
      "school": "School/University Name",
      "location": "Location",
      "date": "Graduation Date",
      "details": ["Detail 1", "Detail 2"]
    }}
  ],
  "leadership": [
    {{
      "title": "Position Title",
      "organization": "Organization Name",
      "location": "Location",
      "date": "Date",
      "bullets": ["Role responsibility 1", "Role responsibility 2"]
    }}
  ],
  "skills": [
    {{
      "category": "Skill Category",
      "items": ["Skill 1", "Skill 2", "Skill 3"]
    }}
  ],
  "certifications": [
    {{
      "name": "Certification Name",
      "date": "Date Earned"
    }}
  ]
}}

IMPORTANT:
- ALL text fields must contain the complete, untruncated content
- ALL sections present in the resume must be included
- Do not omit or abbreviate work experience bullets
- Do not abbreviate project descriptions
- Return only the JSON object, nothing else"""


def resume_polish_prompt(resume_text: str, mode: str = "medium") -> str:
    """Generate a prompt to polish an entire resume"""
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


def get_changes_summary_prompt(original, polished):
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

def job_tailor_prompt(resume_section: str, job_description: str, intensity: str = "medium") -> str:
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

def experience_updater_prompt(user_input: str) -> str:
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
def get_grader_prompt(resume_text: str) -> str:
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


def parse_resume_structure_prompt(resume_text: str) -> str:
    return f"""You are a resume parsing expert. Your task is to recognize common resume formatting patterns and extract structured data.

RESUME:
{resume_text}

===== CRITICAL INSTRUCTIONS =====

CRITICAL FIRST STEP - EXTRACT CONTACT INFORMATION:
At the very top of most resumes is the candidate's contact information. Look for:
1. NAME: Usually the first line or near the top, typically centered and in larger font
   - Extract the person's full name (e.g., "John Smith", "Jane Doe")
2. EMAIL: Look for text with @ (e.g., "john@example.com")
3. PHONE: Look for patterns like (123) 456-7890, 123-456-7890, +1 123 456 7890
4. LOCATION: City, State or City, Country (e.g., "San Francisco, CA", "New York, NY")
5. LINKEDIN: URLs containing "linkedin.com" (extract just URL or extracted text)
6. GITHUB: URLs containing "github.com" (extract just URL or extracted text)
7. WEBSITES/PORTFOLIO: Other URLs (portfolio.com, personalwebsite.dev, etc.)
   - Store these in a "websites" object with keys like: {{"portfolio": "portfolio.com", "website": "example.com"}}

Put ALL contact information in a "contact" object at the top of the JSON. Missing fields should be null.

CRITICAL - ALWAYS EXTRACT EDUCATION:
NO MATTER HOW MANY OTHER SECTIONS ARE PRESENT, you MUST extract ANY education section found.
Education typically appears after contact info and before or after skills section.
Look for "EDUCATION" header and extract ALL education entries found.
This is mandatory - do not skip education even if other sections take priority.

===== SECTION PATTERNS =====

1. WORK EXPERIENCE / PROFESSIONAL EXPERIENCE / EMPLOYMENT:
   - Typical format: "Title/Position – Company/Organization [Location] [Date Range]"
   - Can also appear as separate lines or multiple formats
   - Each entry has: a job title, a company/organization name, optional location, optional dates, and bullet points describing accomplishments
   - Locations can be cities, states, or "Remote"
   - Dates are typically in format: "Month Year – Month Year" or "Month Year – Present"

2. PROJECTS / ACADEMIC PROJECTS / PERSONAL PROJECTS:
   - Typical format: "Project Name [| Technology Stack]"
   - Location: Projects rarely have locations unless specified
   - Dates: May not have dates
   - Technologies: Often listed inline with project name (after | or parentheses)
   - Each project has bullet points describing what was built/accomplished

3. LEADERSHIP / ACTIVITIES / INVOLVEMENT / EXTRACURRICULARS:
   - Typical format: "Title – Organization [Location] [Date Range]"
   - Similar to work experience but for clubs, organizations, volunteering
   - Has: a title, organization name, optional location, optional dates, bullet points

4. EDUCATION:
   - Section header: Usually labeled "EDUCATION", "EDUCATION & TRAINING", "ACADEMIC BACKGROUND", etc.
   - Typical format: "School/University [Location] [Date]" with degree info on same or next line
   - Common patterns:
     * "School Name [Location] [Date]" followed by "Degree | Major | Details"
     * "Degree – School Name" format
     * Line 1: School name and date, Line 2: Degree and major
   - Date may appear on same line as school or on separate line
   - Can appear early in resume (after contact) or later
   - ALWAYS extract if present - this is important!

5. SKILLS / TECHNICAL SKILLS / COMPETENCIES:
   - Usually listed as categories with items underneath
   - May be comma-separated or bullet-pointed
   - Extract category names and skill items

EXTRACTION RULES - DO NOT HARDCODE:
- Look for PATTERNS not specific keywords. For example:
  - "Title/Position – Company" format indicates work experience entry
  - "Name [| Technology]" on its own line often indicates a project
  - "Title – Organization" in a leadership/activity section
  - "School Name [Location] [Date]" with "Degree | Major" on next line indicates education entry
  - Section headers like "EDUCATION", "SCHOOL", "ACADEMIC BACKGROUND" mark education sections
  
- For locations: Extract only if explicitly shown in the HEADER line of an entry (not from bullet content)
  - Locations appear after a dash, comma, or in parentheses near the title/company
  - Do NOT infer locations from bullet points

- For dates: Extract only if explicitly shown in the HEADER line (not from bullet content)
  - Typically at the end of an entry header
  - Format: "Month Year – Month Year" or "Month Year – Present" or "Month Year" or range formats like "Aug 2025 - May 2027"

- For bullets: Extract EVERY bullet point exactly as written
  - has_location in bullet: true ONLY if the bullet text itself contains a location mention (city, state, address)
  - has_date in bullet: true ONLY if the bullet text itself contains a date or time period

- For company/organization names: Extract exactly as they appear in the resume, do NOT set to null if present
- For technologies in projects: Extract inline technologies if listed (e.g., "Python", "React", "JavaScript")
- For education details: Any additional information (GPA, honors, coursework) goes in details array

Return ONLY valid JSON with no explanation, markdown formatting, or code blocks - just pure JSON:

{{
  "contact": {{
    "name": "string (required - extract from resume top)",
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null (City, State or City, Country)",
    "linkedin": "string or null (full URL or extracted text)",
    "github": "string or null (full URL or extracted text)",
    "portfolio": "string or null (portfolio/personal website URL)",
    "websites": {{}} "additional site names to URLs"
  }},
  "work_experience": [
    {{
      "position": "string",
      "company": "string",
      "location": "string or null",
      "start_date": "string or null",
      "end_date": "string or null",
      "bullets": [
        {{"text": "string", "has_location": false or true, "has_date": false or true}}
      ]
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "location": "string or null",
      "date": "string or null",
      "technologies": "string or null",
      "bullets": [
        {{"text": "string", "has_location": false or true, "has_date": false or true}}
      ]
    }}
  ],
  "leadership": [
    {{
      "title": "string",
      "organization": "string or null",
      "location": "string or null",
      "date": "string or null",
      "bullets": [
        {{"text": "string", "has_location": false or true, "has_date": false or true}}
      ]
    }}
  ],
  "education": [
    {{
      "degree": "string",
      "school": "string",
      "location": "string or null",
      "date": "string or null",
      "details": [
        {{"text": "string"}}
      ]
    }}
  ],
  "skills": [
    {{
      "category": "string",
      "items": ["string"]
    }}
  ]
}}

PARSED RESUME:"""


def parse_resume_to_pdf_format_prompt(resume_text: str) -> str:
    """
    Parse resume into the exact structure needed by generate_resume.py for PDF generation.
    This is optimized for simplicity and direct PDF output without intermediate transformations.
    """
    return f"""You are a resume parsing expert. Extract structured data from this resume in the EXACT format needed for PDF generation.

RESUME TO PARSE:
{resume_text}

===== EXTRACTION RULES =====

1. NAME: Extract the person's full name from the top of the resume.

2. CONTACT: Create an HTML-formatted string with email, phone, LinkedIn, GitHub, and portfolio.
   - Format: '<link href="mailto:email@example.com"><u>email@example.com</u></link> | (123) 456-7890 | <link href="https://linkedin.com/in/profile"><u>www.linkedin.com/in/profile</u></link> | <link href="https://github.com/user"><u>github.com/user</u></link>'
   - Use mailto: for email
   - Include phone as plain text
   - Include LinkedIn, GitHub, and portfolio URLs as clickable links
   - Order: email | phone | linkedin | github | portfolio
   - Only include contact items that are present in the resume
   - Use self-closing link tags: <link href="URL"><u>display text</u></link>

3. EDUCATION: For each education entry
   - "school": School/University name
   - "dates": Date range (e.g., "Aug 2023 - May 2027" or "2020 - 2024")
   - "detail": Degree, major, GPA, honors as a single string (e.g., "Bachelors of Science in Computer Science | GPA: 3.8 / 4.0")

4. TECHNICAL_SKILLS: Array of (label, value) tuples grouped by category
   - Each tuple is: [label, comma-separated skills]
   - Example: ["<b>Programming Languages</b>", "Python, C/C++, SQL, Java"]
   - Example: ["<b>AI/ML</b>", "LLM Integration, Prompt Engineering, Machine Learning"]
   - Group skills logically by category (Languages, AI/ML, Data, Tools, Soft Skills, etc.)
   - Preserve any <b> tags for category labels
   - Extract EVERY skill mentioned in the resume

5. WORK_EXPERIENCE: For each job
   - "title": Job title/position
   - "company": Company/Organization name
   - "dates": Date range (e.g., "Dec 2025 – Present" or "Feb 2023 – Dec 2024")
   - "bullets": Array of accomplishment bullets
     * Each bullet should be complete sentence/accomplishment
     * Include any bold text formatting from original (e.g., "<b>40%</b>")
     * Do NOT include leading "- " or "bullet" markers
     * Extract EXACTLY as written in the resume

6. PROJECTS: For each project
   - "name": Project name/title
   - "tech": Technologies/stack used (comma-separated, e.g., "Python, Ollama, LLaMA 3")
   - "bullets": Array of accomplishment bullets
     * Same formatting rules as work experience
     * Extract exactly as written

7. LEADERSHIP: For each leadership/activity role
   - "title": Role/title (e.g., "Secretary", "President", "Volunteer")
   - "org": Organization name
   - "dates": Date range (e.g., "Sep 2025 – Present")
   - "bullets": Array of accomplishment bullets
     * Same formatting rules as work experience

===== IMPORTANT RULES =====
- Extract ALL content from the resume (don't skip sections)
- Preserve all HTML formatting (<b>, <u>, <i>, links) from original
- Do NOT invent or modify details - extract exactly as written
- For skill values, separate items with commas: "Python, Java, C++"
- Do NOT use [N/A] or placeholder text
- Order sections as: name, contact, education, technical_skills, work_experience, projects, leadership
- Return ONLY valid JSON with no explanation, no markdown, no code blocks

===== JSON STRUCTURE =====
Return exactly this structure (omit empty arrays/objects):

{{
  "name": "string",
  "contact": "html string with links",
  "education": [
    {{"school": "string", "dates": "string", "detail": "string"}},
    ...
  ],
  "technical_skills": [
    ["<b>Category</b>", "skill1, skill2, skill3"],
    ...
  ],
  "work_experience": [
    {{
      "title": "string",
      "company": "string",
      "dates": "string",
      "bullets": ["bullet1", "bullet2", ...]
    }},
    ...
  ],
  "projects": [
    {{
      "name": "string",
      "tech": "string",
      "bullets": ["bullet1", "bullet2", ...]
    }},
    ...
  ],
  "leadership": [
    {{
      "title": "string",
      "org": "string",
      "dates": "string",
      "bullets": ["bullet1", "bullet2", ...]
    }},
    ...
  ]
}}

BEGIN EXTRACTION (return only valid JSON):"""