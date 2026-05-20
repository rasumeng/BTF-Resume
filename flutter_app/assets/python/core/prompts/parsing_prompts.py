"""
Resume parsing prompts for extracting structured data from resumes.
"""


def parse_resume_structure_prompt(resume_text: str) -> str:
    """
    Generate a prompt to parse resume text into structured JSON.
    
    Args:
        resume_text: Resume text to parse
        
    Returns:
        Complete prompt for LLM to return structured resume JSON
    """
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


def parse_to_pdf_format_prompt(resume_text: str) -> str:
    """
    Generate a prompt to parse resume text into PDF-format JSON.
    
    Args:
        resume_text: Resume text to parse
        
    Returns:
        Complete prompt for LLM
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


def parse_resume_to_pdf_format_prompt(resume_text: str) -> str:
    """
    Parse resume into the exact structure needed by generate_resume.py for PDF generation.
    This is optimized for simplicity and direct PDF output without intermediate transformations.
    
    Args:
        resume_text: Resume text to parse
        
    Returns:
        Complete prompt for LLM
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
   - Group skills logically by category (Languages, AI/ML, Data, Tools, Soft Skills, etc.)"""
