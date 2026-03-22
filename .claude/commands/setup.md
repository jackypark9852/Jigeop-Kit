Run the First-Time Setup workflow for this job application workspace.

This command guides the user from a fresh clone to a fully operational workspace with deep
project analysis. It is safe to re-run at any time — completed phases are skipped automatically.

---

## Phase 1 — Dependency check

1. Check Python dependencies by running:
   ```
   python -c "import jinja2, yaml, fitz, bs4, questionary; print('OK')"
   ```
   If the import fails, run `pip install -e .` and then verify again.
   If `questionary` is still missing after that, run `pip install questionary>=2.0` separately.

2. Check pdflatex:
   ```
   pdflatex --version
   ```
   If missing, show the user these OS-specific instructions and **wait for them to install before continuing**:
   - **Windows**: Download and install MiKTeX from https://miktex.org/download
     (enable "Install missing packages on the fly" in the installer)
   - **Mac**: `brew install --cask mactex-no-gui`
   - **Linux**: `sudo apt install texlive-latex-base texlive-fonts-recommended texlive-latex-extra`

---

## Phase 2 — Profile creation

Guard: if `profile/resume.yaml` already exists, ask the user whether to skip or rebuild.
If they say skip, jump to Phase 3.

**This phase is entirely file-driven. Never ask the user to list projects, skills,
experience, or preferences. Extract everything from the files they provide.**

### Step 2a — Open file picker

Run this Python one-liner to open a native multi-select file picker:

```
python -c "
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.wm_attributes('-topmost', True)
paths = filedialog.askopenfilenames(
    title='Select your resume(s) — PDF, DOCX, or TXT (multiple OK)',
    filetypes=[('Resume files', '*.pdf *.docx *.txt'), ('All files', '*.*')]
)
for p in paths:
    print(p)
"
```

Capture each line of stdout as a selected file path.

If the user cancels (no output), tell them to place their resume in `profile/raw/resumes/`
and re-run `/setup`. Do not fall back to asking questions.

### Step 2b — Copy files

For each selected path, copy the file into `profile/raw/resumes/` (create the directory if
it doesn't exist):
```
python -c "import shutil, pathlib; pathlib.Path('profile/raw/resumes').mkdir(parents=True, exist_ok=True); shutil.copy('<path>', 'profile/raw/resumes/')"
```

### Step 2c — Extract profile

Run `python scripts/ingest.py resume profile/raw/resumes/<filename>` on the primary file
(largest or most complete if multiple were selected).

If multiple files were selected (e.g., English resume + LinkedIn export), read all of them
and merge any additional information into `resume.yaml` — extra projects, skills, or
experience entries that appear in the secondary files but not the primary.

### Step 2d — Review and finalize

Read the extracted `profile/resume.yaml`. For each of the following fields that is clearly
missing AND could not be inferred from the files, ask **at most one targeted question**:
- `github` (GitHub username or URL)
- `linkedin` (LinkedIn profile URL)
- `phone` / `email` (if not in the resume)

Never ask the user to list or re-describe projects, skills, bullets, education, or
work experience — these must come from the extracted file.

### Step 2e — Expand skills_pool

After finalizing `resume.yaml`, expand the `skills_pool` section: for every technical term
found in `skills`, `projects`, and `experience` bullets, add it to the appropriate
`skills_pool` category. The pool should be comprehensive — include synonyms and related
tools (e.g., if they list "React", also add "React.js", "JSX" if seen in bullets).

---

## Phase 3 — GitHub data + writing voice

1. Run `python scripts/fetch_github.py <github-username>` using the username from
   `profile/resume.yaml`. This populates `profile/raw/github/`.

2. Read the README files in `profile/raw/github/` and any files in
   `profile/raw/writing_samples/` (if present).

3. Derive the user's writing voice from the observed text — tone, sentence length,
   vocabulary level, use of passive vs. active voice, technical density.
   Do NOT ask the user to describe their style.

4. Write `profile/style.md` with:
   ```markdown
   # Writing Voice

   ## Observed Style
   [2-4 sentences describing the patterns you saw across READMEs and writing samples]

   ## Tone
   [e.g., "Direct and technical, favors short declarative sentences"]

   ## Vocabulary
   [e.g., "Comfortable with domain jargon; avoids buzzwords"]

   ## What to Avoid
   [Patterns that would break consistency — e.g., overly formal phrases not seen in samples]
   ```

---

## Phase 4 — Deep project analysis (CORE)

This is the most important phase. It generates an `analysis.md` for every project,
which powers genuinely targeted bullet writing and ATS keyword selection in `/tailor`.

### Step 4a — Clone repos

Run `python scripts/clone_repos.py`

This shallow-clones all project and contribution repos from `resume.yaml` into
`profile/raw/projects/repos/<slug>/`.

### Step 4b — Analyze each project

For each project and contribution entry in `profile/resume.yaml` that has a `url`
pointing to a GitHub repo:

1. Derive the slug: last path segment of the URL, lowercased, spaces → hyphens.
   Example: `https://github.com/user/CUDA-Path-Tracer` → slug = `cuda-path-tracer`

2. If `profile/raw/projects/<slug>/analysis.md` already exists, **skip it** (do not overwrite).

3. Read the cloned repo at `profile/raw/projects/repos/<slug>/`:
   - Always read `README.md`
   - Read key source files that contain the most interesting algorithms, data structures,
     or core logic. Prioritize depth over breadth — 3 well-read files beat 15 skimmed ones.
   - For contributions: also read `my_commits.txt` (generated by `clone_repos.py`) to
     understand exactly which code the user authored.

4. Generate `profile/raw/projects/<slug>/analysis.md` in **exactly** this format:

```markdown
# <Project Name> — Technical Analysis
_Tech: <stack> | Dates: <dates from resume.yaml> | Repo: <url>_

## What It Does
[1-3 sentences: purpose, audience, core capability]

## Key Algorithms & Techniques
[Subsections per major technical component. Name the exact algorithm or technique.
Include complexity where relevant.]

## Architecture & Data Structures
[Key structs/classes, file organization, data flow between components]

## Performance Characteristics
[Measured numbers if available — frame times, speedups, scale. Omit if not measured.]

## Technical Challenges & Solutions
[2-5 non-obvious problems and how they were solved]

## Talking Points by Role
[2-3 subsections for the role types this project is most relevant to.
Each subsection: 2-4 resume-ready bullet sentences using specific technical language.]

## ATS Keywords
**Languages/APIs:** [comma-separated exact terms]
**Techniques:** [algorithms, patterns, methods used]
**Tools:** [profiling tools, IDEs, external SDKs]
**Concepts:** [broader categories — "real-time rendering", "GPU optimization", etc.]
```

### Step 4c — Report

List each project analyzed and the path to its `analysis.md`. Note any projects skipped
(already existed) and any skipped due to no URL or missing cloned repo.

---

## Phase 5 — Smoke-test render

1. Write a minimal test context YAML at `output/_setup-test/resume-context.yaml`:
   ```yaml
   output_filename: _setup-test
   name: <user's name from resume.yaml>
   email: <user's email>
   phone: ""
   location: ""
   linkedin: ""
   github: ""
   education: <copy education from resume.yaml>
   experience: []
   skills: {languages: [], frameworks: [], tools: [], platforms: []}
   projects: []
   ```

2. Run:
   ```
   python scripts/render.py resume output/_setup-test/resume-context.yaml --max-pages 1
   ```

3. If exit code 0: delete `output/_setup-test/` and report success.
4. If it fails: diagnose the error (missing LaTeX packages, path issues, etc.) and fix
   before declaring setup complete. Do not move on with a broken render pipeline.

---

## Phase 6 — Ready summary

Tell the user setup is complete. Show this table:

```
✓ profile/resume.yaml        master profile
✓ profile/style.md           writing voice
✓ profile/raw/github/        GitHub data
✓ profile/raw/projects/      project analysis files

Commands available:
  /tailor <job-url-or-file>   Tailor your resume for a specific job
  /setup                      Re-run setup (e.g., add a new project analysis)

Natural language triggers:
  "write a cover letter for jobs/X.md"  → cover-letter.pdf
  "ATS analysis for jobs/X.md"          → keyword gap report
  "full application for jobs/X.md"      → resume + cover letter + ATS report
  "save this job: <url or paste>"       → saves JD to jobs/
```
