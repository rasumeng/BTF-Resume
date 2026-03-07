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



if __name__ == "__main__":
    text = load_resume("samples/resume.txt")
    sections = parse_section(text)
    for header, content in sections.items():
        print(f"--- {header} ---")
        print(content)
        print()