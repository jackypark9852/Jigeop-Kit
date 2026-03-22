# Job Application Workspace

A Claude Code workspace that tailors resumes and cover letters to specific job descriptions.
Tell Claude which job you're applying for — it reads your profile, analyzes the JD, and
produces a targeted PDF resume and cover letter in minutes.

## What It Does

- **Tailors resumes** — rewrites and reorders bullets to match each job's keywords and priorities
- **Writes cover letters** — in your voice, grounded in your real experience
- **ATS analysis** — flags missing keywords and suggests rewrites before you apply
- **Tracks applications** — one markdown file per job keeps everything organized

## Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/claude-code)
- Python 3.11+
- pdflatex — [MiKTeX](https://miktex.org) (Windows), `brew install --cask mactex-no-gui` (Mac),
  or `sudo apt install texlive-latex-base texlive-fonts-recommended` (Linux)

## Setup

```bash
# 1. Use this template on GitHub → clone your new repo
git clone https://github.com/your-username/your-repo-name
cd your-repo-name

# 2. Install Python dependencies
pip install -e .

# 3. Open Claude Code and start talking
claude
```

On first run, Claude detects that your profile doesn't exist yet and walks you through
building it conversationally — no manual YAML editing required.

## Usage

Once your profile is set up, just talk to Claude:

```
"save this job description: [paste JD]"
"tailor my resume for jobs/stripe-sre.md"
"write a cover letter for jobs/stripe-sre.md"
"what keywords am I missing for jobs/stripe-sre.md"
"full application for jobs/stripe-sre.md"
```

See `CLAUDE.md` for the complete workflow reference.

## Optional: Deep Project Analysis

For technical roles where project depth matters, you can clone your project repos and
have Claude analyze them for role-specific talking points:

```bash
# After profile/resume.yaml is set up:
python scripts/clone_repos.py          # clone all repos listed in resume.yaml
# Then ask Claude to analyze a project:
# "analyze profile/raw/projects/repos/my-project and write an analysis.md"
```
