def load_resume(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as file:
        text = file.read()
    return text

def parse_section(text: str) -> dict:
    sections = {}
    current_section = None
    lines = text.split("\n")
    for line in lines:
        if line.strip().isupper():
            current_section = line.strip()
            sections[current_section] = ""
        else:
            if current_section is None:
                continue
            sections[current_section] += line.strip() + "\n"
    return sections

def parse_subsectiontions(section_text: str) -> list:
    subsections = []
    current = None
    lines = section_text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            #empty line - skip it
            pass
        # Bullet Branch
        elif line.startswith("*") or line.startswith("-"):
            if current is not None:
                clean = line.lstrip("*- ").strip()
                current["bullets"].append(clean)
    
        # Title
        else:
            if current is not None:
                subsections.append(current)
            current = {"title": line, "bullets": []}
    # save the last subsection
    if current is not None:
        subsections.append(current)
    
    return subsections


if __name__ == "__main__":
    text = load_resume("samples/resume.txt")
    sections = parse_section(text)
    subsections = parse_subsectiontions(sections["PROJECTS"])
    for sub in subsections:
        print(sub["title"])
        for bullet in sub["bullets"]:
            print(" -", bullet)
        print()