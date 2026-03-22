Run Workflow 2 (Write a Cover Letter) from CLAUDE.md for the following job: $ARGUMENTS

If $ARGUMENTS is a file path (e.g. jobs/stripe-sre.md), read that file for the job description.
If $ARGUMENTS is a URL, fetch the page content and extract the job description from it.
If $ARGUMENTS is empty, ask which job to write a cover letter for before proceeding.

Follow the workflow steps exactly:
1. Read `profile/resume.yaml`, `profile/style.md`, and `profile/cover_letter_guide.md`
2. Read the job description
3. Analyze the JD: extract role needs, company signals, culture indicators, and ATS keywords
4. Research the company: use web search and web fetch to find their engineering blog,
   product pages, recent news, and team info. This is what makes the letter genuine —
   spend effort here. Look for:
   - Specific products, features, or technical challenges they work on
   - Recent blog posts, talks, or open-source projects
   - Company mission, values, or culture statements
   - The specific team or department this role belongs to
5. If `output/<slug>/resume-context.yaml` exists, read it to know what's already on the
   tailored resume. Use complementary angles in the cover letter — don't repeat the same
   highlights. The cover letter should add context the resume cannot.
6. Generate `output/<slug>/cover-letter-proposal.yaml` with three sections:
   ```yaml
   hooks:
     - name: "Achievement: [specific achievement from profile]"
       reason: "Why this hook works for this JD"
       checked: true   # recommend exactly 1 hook as checked
     - name: "Company-knowledge: [specific thing about this company]"
       reason: "Shows genuine engagement with their work"
       checked: false
     - name: "Shared-mission: [alignment with company values]"
       reason: "Values match for culture-fit roles"
       checked: false
   achievements:
     - name: "[Project/experience] — [key metric or outcome]"
       reason: "Maps to JD requirement X"
       checked: true   # recommend 1-2 achievements as checked
     - name: "[Another project/experience]"
       reason: "..."
       checked: false
   company_angles:
     - name: "[Specific blog post, product, or initiative]"
       reason: "Technical overlap with user's experience"
       checked: true   # recommend exactly 1 angle as checked
     - name: "[Alternative angle]"
       reason: "..."
       checked: false
   ```
   Include 2-3 hooks, 3-4 achievements, and 2-3 company angles.
   Achievements should come from both `experience[]` and `projects[]` in resume.yaml.
7. Run: `python scripts/select_items.py output/<slug>/cover-letter-proposal.yaml -o output/<slug>/cover-letter-selection.yaml`
   This launches an interactive terminal picker. Wait for it to complete.
8. Read the selection. Write the 3-paragraph cover letter following `cover_letter_guide.md`:
   - **P1 — Hook (75-85 words):** Use the selected hook approach. Include exact role name
     and company name. Reference the selected company angle. Open with specificity,
     not "I am writing to apply..."
   - **P2 — Proof (100-125 words):** Build from the selected achievements. Quantified impact,
     specific technologies, connection to JD needs. Don't repeat resume verbatim — add
     context, motivation, and "why it matters for this role." Mention at least one
     collaboration detail.
   - **P3 — Close (50-60 words):** Confident tone (not desperate). Clear call to action
     (not "I look forward to hearing from you"). Restate enthusiasm for the specific role.
   - Match `style.md` voice throughout. No buzzwords. Sound like a person, not a template.
   - Total: 250-400 words, must fit one page.
9. Present the full draft to the user as formatted text. Show paragraph labels (Hook, Proof,
   Close) and word count. Ask: "Ready to render, or would you like changes?"
10. If the user requests changes: iterate on the draft, re-present. Repeat until approved.
11. On approval: write `output/<slug>/cover-letter-context.yaml` with this schema:
    ```yaml
    output_filename: <slug>
    name: ...          # from resume.yaml
    email: ...
    phone: ...
    location: ...
    date: "<today's date, e.g. March 22, 2026>"
    hiring_manager: "" # leave blank if unknown — template omits it
    company: <company name>
    role: <role title>
    greeting: "Dear Hiring Team"  # or "Dear [Name]" if known
    body:
      - "<paragraph 1 text>"
      - "<paragraph 2 text>"
      - "<paragraph 3 text>"
    closing: "Best regards"
    ```
12. Run: `python scripts/render.py cover_letter output/<slug>/cover-letter-context.yaml`
13. Report where the PDF and `.tex` landed. The user can edit the `.tex` and recompile manually.
