# BTF Resume

A free, local AI resume helper that polishes your resume bullets, tailors your resume to job descriptions, and formats new experience — all running privately on your own machine. No API keys, no subscriptions, no data leaving your device.

---

## Why BTF Resume?

Most AI resume tools cost money, require an account, or send your personal data to external servers. This is my take on a free alternative — built from scratch in Python, powered by open-source LLMs that run entirely on your device.

---

## Features

- **Bullet Polish** — rewrites weak resume bullets into strong, ATS-optimized ones using proven resume writing formulas
- **Job Tailoring** — aligns your resume language and keywords to match a specific job description without changing your real experience
- **Experience Updater** — describe a new project or role in plain English and get polished, formatted resume bullets back
- **PDF + TXT input** — works with both plain text and real PDF resumes
- **PDF output** — generates a clean, formatted PDF resume ready to send
- **100% offline** — no internet connection required after setup, no API keys, completely free

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.10+ |
| LLM Runtime | [Ollama](https://ollama.com) |
| Bullet Polish Model | Mistral 7B (fast, efficient) |
| Job Tailoring Model | LLaMA 3 8B (stronger instruction following) |
| PDF Reading | pdfplumber |
| PDF Generation | ReportLab |
| CLI | argparse |

> Smart model routing — uses Mistral for simple tasks and LLaMA 3 for complex ones, balancing speed and quality.

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed on your machine
- 8GB+ RAM recommended

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/rasumeng/BTF-Resume.git
cd BTF-Resume
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Install Ollama and pull models**
```bash
# Install Ollama from https://ollama.com
ollama pull mistral
ollama pull llama3
```

**5. Make sure Ollama is running**
```bash
ollama serve
```

---

## Usage

### Polish your resume bullets
```bash
python main.py --resume samples/resume.txt
```

### Tailor your resume to a job description
```bash
python main.py --resume samples/resume.txt --job samples/job.txt
```

### Add a new experience to your resume
```bash
python main.py --resume samples/resume.txt --add-experience
```

### Combine flags
```bash
python main.py --resume samples/resume.pdf --job samples/job.txt --output outputs/my_resume.pdf
```

> Both `.txt` and `.pdf` resume files are supported.

---

## Project Structure

```
BTF-Resume/
├── main.py               # CLI entry point
├── llm_client.py         # Ollama API wrapper with model routing
├── prompts.py            # All prompt templates
├── input_parser.py       # Resume file reader and section parser
├── output_builder.py     # AI pipeline and section assembler
├── pdf_generator.py      # PDF output generator
├── samples/
│   ├── resume.txt        # Sample resume input
│   └── job.txt           # Sample job description
├── outputs/              # Generated PDFs
├── requirements.txt
└── README.md
```

---

## How It Works

```
Resume File (.txt or .pdf)
        ↓
  Input Parser — extracts and splits resume into sections
        ↓
  Output Builder — routes each section through the right AI prompt
        ↓
  Ollama (Local LLM) — Mistral or LLaMA 3 depending on task
        ↓
  PDF Generator — assembles and outputs a clean PDF resume
```

---

## Roadmap

- [ ] Web frontend with drag-and-drop resume upload
- [ ] Cover letter generator
- [ ] LinkedIn summary generator
- [ ] Optional cloud LLM support (Claude / GPT-4) for higher quality output
- [ ] Resume scoring and ATS compatibility checker

---

## Author

Built by Robert Asumeng
[LinkedIn](https://www.linkedin.com/in/robertasumeng) | [GitHub](https://github.com/rasumeng)
