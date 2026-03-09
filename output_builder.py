from input_parser import parse_section, parse_subsectiontions
from prompts import bullet_polish_prompt
from llm_client import ask_llm

SECTIONS_TO_POLISH = ["WORK EXPERIENCE", "PROJECTS", "LEADERSHIP"]


def build_resume(sections: dict) -> dict:
    improved_sections = {}
    for section, content in sections.items():
        if section in SECTIONS_TO_POLISH:
            prompt = bullet_polish_prompt(content)
            polished_content = ask_llm(prompt)
            polished_content = clean_bullets(polished_content)
            improved_sections[section] = polished_content
        else:
            improved_sections[section] = content
    return improved_sections    

def polish_section(section_text: str) -> str:
    improved_subsections = []
    for sub in section_text:
        pass

def clean_bullets(text: str) -> str:
    lines = text.strip().split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if line:
            # Remove leading numbers like "1." "2." etc
            if line[0].isdigit() and line[1] in ".):":
                line = "- " + line[2:].strip()
            cleaned.append(line)
    return "\n".join(cleaned)

if __name__ == "__main__":
    from input_parser import load_resume
    
    text = load_resume("samples/resume.txt")
    sections = parse_section(text)
    improved = build_resume(sections)
    
    for header, content in improved.items():
        print(f"--- {header} ---")
        print(content)
        print()
