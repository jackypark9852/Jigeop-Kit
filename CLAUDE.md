# Job Application Workspace

You are helping the user apply for jobs. Your job is to read their profile,
understand the target role, and produce tailored application materials.

**Before anything else**: check if `profile/resume.yaml` exists. If it does not, tell
the user to run `/setup` to get started. Do not proceed with any other workflow until
setup is complete.

## Repo Layout

```
profile/
  resume.yaml          ← master profile (always read this first)
  style.md             ← writing voice + samples (read when writing cover letters)
  raw/
    resumes/           ← original resume PDFs for reference
    writing_samples/   ← blog posts, emails, essays that capture their voice
    github/            ← GitHub profile exports, README files
    websites/          ← personal site or LinkedIn exports
    projects/          ← per-project deep analysis files (analysis.md)

jobs/
  _template.md         ← frontmatter template for new job files
  <company>-<role>.md  ← one file per job (frontmatter + full JD)

templates/
  resume.tex.j2        ← LaTeX resume template (Jinja2, \VAR{} delimiters)
  cover_letter.tex.j2  ← LaTeX cover letter template
  jinja_env.py         ← Jinja2 environment helper

scripts/
  render.py            ← renders context YAML → PDF (you call this)
  ingest.py            ← extracts text from raw sources (user calls this)
  fetch_github.py      ← fetches GitHub profile data (user runs once at setup)
  clone_repos.py       ← clones project repos for deep analysis (optional)

output/
  <job-slug>/          ← one folder per job application
    resume.tex           ← editable LaTeX source
    resume.pdf
    cover-letter.tex
    cover-letter.pdf
    resume-context.yaml
    cover-letter-context.yaml
```

## PDF Rule — Never Read PDFs Directly

Reading a PDF file uses significantly more tokens than reading plain text.
Every PDF in `profile/raw/` should have a `.txt` sidecar alongside it.

Before reading any `.pdf` file:
1. Check if `<same-path>.txt` exists.
2. If yes → read the `.txt` file instead.
3. If no → run `python scripts/pdf_to_text.py <path-to-pdf>`, then read the `.txt`.

Example: `profile/raw/resumes/resume.pdf` → read `profile/raw/resumes/resume.txt`

## Workflows

### 0. First-Time Setup

**Triggered by**: `/setup` slash command (or user asking "how do I get started?")

Run the `/setup` slash command. It walks through all setup phases automatically:
1. Dependency check (Python packages + pdflatex)
2. Profile creation — opens a file picker to select existing resume(s); extracts
   `profile/resume.yaml` from the files without asking the user to re-list anything
3. GitHub data fetch + writing voice derivation from READMEs
4. Deep project analysis — clones repos and generates `profile/raw/projects/<slug>/analysis.md`
   for every project with a GitHub URL (the core differentiator of this workflow)
5. Smoke-test render to confirm the full pipeline works
6. Summary of available commands

Re-running `/setup` is safe — completed phases (existing `resume.yaml`, existing `analysis.md`
files) are skipped automatically. Run it again after adding a new project to generate its analysis.

---

### 1. Tailor a Resume

_Guard: If `profile/resume.yaml` doesn't exist, tell the user to run `/setup` first._

Triggered by: "tailor my resume for this job", "generate a resume for jobs/X.md"

Steps:
1. Read `profile/resume.yaml` — this is the master profile.
2. Read the job description (from a file in `jobs/` or pasted by the user).
3. Analyze the JD: extract required skills, preferred skills, key responsibilities,
   company values, and ATS keywords.
4. For each project in the resume, check if `profile/raw/projects/<slug>/analysis.md`
   exists — if so, read it for role-specific talking points before writing bullets.
5. Read `profile/bullet_guide.md` for bullet writing best practices.
6. Build the tailored skills section from `profile/resume.yaml` `skills_pool`:
   - Cross-reference `skills_pool` against the JD's ATS keywords
   - For each selected project, check its `analysis.md` ATS Keywords section for
     additional signal keywords justified by that project's work
   - Within each category, front-load JD-matching keywords; reorder categories to
     put the highest-signal one first for this role
   - Remove keywords with no JD relevance to keep the section concise
7. Decide what to emphasize:
   - Reorder/rewrite experience bullets to front-load the most relevant ones.
   - Trim bullets from less-relevant roles if needed to keep it to one page.
   - Do NOT invent experience — only amplify and reframe what's in the profile.
   - Apply the XYZ formula, action verb variety, and quantification guidelines
     from the bullet guide when writing or rewriting bullets.
8. Write a context YAML at `output/<company>-<role>/resume-context.yaml` with
   the tailored data (same schema as `resume.yaml`, plus an `output_filename` key).
9. Run: `python scripts/render.py resume output/<company>-<role>/resume-context.yaml --max-pages 1`
   This writes both `resume.tex` (editable source) and `resume.pdf` to the output folder.
   If the script warns about overflow (exit code 2), trim bullets or remove a project and re-render.
10. Tell the user where the PDF and `.tex` landed. They can edit the `.tex` and recompile manually.

Context YAML schema:
```yaml
output_filename: stripe-sre  # → output/stripe-sre/resume.pdf
name: ...
email: ...
phone: ...
location: ...
linkedin: ...
github: ...
website: ...
experience:
  - company: ...
    title: ...
    location: ...
    dates: ...
    bullets:
      - "Rewritten bullet..."
education: [ ... ]
skills:
  languages: [ ... ]
  frameworks: [ ... ]
  tools: [ ... ]
  platforms: [ ... ]
projects: [ ... ]
certifications: [ ... ]
```

### 2. Write a Cover Letter

_Guard: If `profile/resume.yaml` doesn't exist, tell the user to run `/setup` first._

Triggered by: "write a cover letter for jobs/X.md", "cover letter for [company]"

Steps:
1. Read `profile/resume.yaml` and `profile/style.md`.
2. Read the job description.
3. Read `profile/cover_letter_guide.md` for cover letter writing best practices.
4. Study `style.md` carefully — match tone, sentence length, vocabulary level,
   and avoid anything the user says they dislike. The user's style.md preferences
   override the cover letter guide where they conflict.
5. Write a cover letter that:
   - Opens with a specific hook (not "I am writing to apply...")
   - Connects 1-2 concrete achievements to the role's needs
   - Shows genuine interest in this company specifically
   - Closes with a direct, confident ask
   - Stays under one page (3-4 paragraphs)
   - Apply the hook templates, tone guidance, and company-research strategies
     from the cover letter guide.
6. Write a context YAML at `output/<company>-<role>/cover-letter-context.yaml`.
7. Run: `python scripts/render.py cover_letter output/<company>-<role>/cover-letter-context.yaml`
8. Tell the user where the PDF landed.

Context YAML schema:
```yaml
output_filename: stripe-sre  # → output/stripe-sre/cover-letter.pdf (same slug as resume)
name: ...
email: ...
phone: ...
location: ...
date: "March 19, 2026"
hiring_manager: ""  # leave blank if unknown — omitted from letter
company: Stripe
role: Site Reliability Engineer
greeting: "Dear Hiring Team"  # or "Dear [Name]" if known
body:
  - "First paragraph text..."
  - "Second paragraph text..."
  - "Third paragraph text..."
closing: "Best regards"
```

### 3. ATS Keyword Analysis

_Guard: If `profile/resume.yaml` doesn't exist, tell the user to run `/setup` first._

Triggered by: "what keywords am I missing", "ATS analysis for jobs/X.md"

Steps:
1. Read `profile/resume.yaml`.
2. Read the job description.
3. Extract all keywords from the JD: technologies, methodologies, soft skills,
   certifications, role-specific jargon.
4. Compare against the profile.
5. Output a structured report:
   - **Present and well-represented** — already prominent in the resume
   - **Present but weak** — mentioned but could be more prominent; suggest where to add
   - **Missing entirely** — not in profile at all; note if it's a must-have or nice-to-have
   - **Suggested rewrites** — specific bullet rewrites to naturally include keywords

### 4. Full Application Package

_Guard: If `profile/resume.yaml` doesn't exist, tell the user to run `/setup` first._

Triggered by: "apply to jobs/X.md", "full application for [company]"

Run workflows 1, 2, and 3 in sequence. Tell the user all three outputs.

### 5. Save a New Job Description

Triggered by: "save this job", "add this job to my list"

1. Create `jobs/<company>-<role>.md` using the `_template.md` frontmatter.
2. Fill in the frontmatter from the JD (company, title, location, url, today's date).
3. Paste the full JD text below the frontmatter.
4. Confirm the filename to the user.

## Profile Notes

- **Projects have bullets**: the `projects[]` in `resume.yaml` include `bullets[]` — use them in
  tailored resumes (the template renders them if present).
- **Project analysis files**: `profile/raw/projects/<slug>/analysis.md` contains deep technical
  analysis of each project including role-specific talking points. When tailoring a resume,
  check for this file first — it enables genuinely targeted bullet generation. Fall back to
  `resume.yaml` bullets if it doesn't exist yet.
- **External contributions**: `resume.yaml` has a `contributions[]` section (same schema as
  `projects[]`) for repos the user contributed to but does not own. When including in a tailored
  resume, slot them into the `projects[]` array of the context YAML so the template renders them.
- **GitHub data**: `profile/raw/github/summary.md` has the full GitHub footprint — read it if
  you need more detail on any project beyond what's in `resume.yaml`.
- **Variant notes**: Add your own notes here as you learn what combinations of projects and
  bullets work best for specific role types. For example: "for backend roles, lead with X;
  for ML roles, emphasize Y." This section is yours to customize.

## Conventions

- **Filenames**: use lowercase kebab-case, e.g. `stripe-sre`, `anthropic-ml-engineer`
- **Never invent facts**: only reframe and reorder what's in `resume.yaml`
- **LaTeX escaping**: the template handles escaping via the `| e` filter — write
  natural text in the context YAML, do not manually escape LaTeX characters
- **Output filenames**: set `output_filename` in the context YAML (no extension)
- **One page rule**: resume should fit one page — trim aggressively if needed
- **Style fidelity**: cover letters must sound like the user, not generic AI prose

## Rendering

The render script requires `pdflatex`. If it fails:
- Check pdflatex is installed: `pdflatex --version`
- Windows: install MiKTeX from miktex.org
- Mac: `brew install --cask mactex-no-gui`
- Linux: `sudo apt install texlive-latex-base texlive-fonts-recommended`

If pdflatex is unavailable, write the `.tex` source to disk and tell the user
they can compile it manually or use Overleaf.
