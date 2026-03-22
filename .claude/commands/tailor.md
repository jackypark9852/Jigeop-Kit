Run Workflow 1 (Tailor a Resume) from CLAUDE.md for the following job: $ARGUMENTS

If $ARGUMENTS is a file path (e.g. jobs/stripe-sre.md), read that file for the job description.
If $ARGUMENTS is a URL, fetch the page content and extract the job description from it.
If $ARGUMENTS is empty, ask which job to tailor for before proceeding.

Follow the workflow steps exactly:
1. Read profile/resume.yaml
2. Read the job description
3. Analyze the JD for required skills, responsibilities, and ATS keywords
4. Check profile/raw/projects/<slug>/analysis.md for any relevant projects before writing bullets
5. Read profile/bullet_guide.md and apply its guidelines when writing bullets (XYZ formula, action verb variety, quantification, length targets)
6. Write a proposal YAML to output/<company>-<role>/proposal.yaml listing ALL projects
   (including contributions[]) and experience entries from resume.yaml. For each item include:
   - name: the project/company name exactly as it appears in resume.yaml
   - reason: one-line explanation of why it is or isn't relevant to this JD
   - checked: true if you recommend including it, false otherwise
   Also add a `keywords` section listing skills_pool keywords that match the JD but are NOT
   explicitly backed by any recommended project's analysis.md ATS Keywords section. These are
   the "borderline" keywords where the user has the capability but no selected project demonstrates
   it directly. Do NOT include keywords that are not in skills_pool.
   checked defaults: true if the connection is reasonable (adjacent tech the user knows); false if weak.
   Example:
   ```yaml
   experience:
     - name: "Alibaba Group"
       reason: "Unreal Engine rendering optimization — directly relevant"
       checked: true
   projects:
     - name: "CUDA Path Tracer"
       reason: "GPU rendering — strong technical signal"
       checked: true
     - name: "OpenClimateFix"
       reason: "React web app — no 3D or game engine relevance"
       checked: false
   keywords:
     - name: "OpenXR"
       reason: "JD requires XR development; in skills_pool (Unity/Unreal support XR) but no dedicated XR project yet"
       checked: true
     - name: "CMake"
       reason: "In skills_pool; not in any recommended project's ATS keywords section"
       checked: false
   ```
7. Run: python scripts/select_items.py output/<company>-<role>/proposal.yaml -o output/<company>-<role>/selection.yaml
   This launches an interactive terminal checkbox picker. Wait for it to complete.
8. Read the selection.yaml output to see what the user chose.
9. Build the tailored skills section:
   a. Read profile/resume.yaml skills_pool — the full keyword pool
   b. For each selected project, read its analysis.md ATS Keywords section for additional signal
   c. Cross-reference with the JD ATS keywords identified in step 3
   d. Select the most relevant subset from skills_pool using two tiers:
      - Tier 1 (auto-include): keyword is in skills_pool AND explicitly listed in
        a selected project's analysis.md ATS Keywords section — include without asking
      - Tier 2 (user-approved extras): keyword appears in selection.yaml `keywords` list
        (user approved it in the picker) — include it
      - Never include: keywords not in skills_pool, regardless of JD match
      - Within each category, front-load JD-matching keywords
      - Reorder categories to put highest-signal categories first for this role
        (e.g., for GPU roles: frameworks before tools; for web roles: languages first)
      - Remove keywords with no JD relevance to keep the section concise
   e. This optimized skills dict replaces the default skills in the context YAML
10. Write a tailored context YAML at output/<company>-<role>/resume-context.yaml
    using only the selected projects and experience entries, with the optimized skills section.
11. Run: python scripts/render.py resume output/<company>-<role>/resume-context.yaml --max-pages 1
12. If the render exits with code 2 (page overflow), the resume is too long.
    Ask the user how they'd like to trim: reduce the number of projects, or shorten bullet text.
    Do NOT silently shorten bullets — that risks losing important technical detail.
    Once the user decides, apply the change, rewrite the context YAML, and re-render.
    Repeat until exit code 0. Do not remove experience bullets or education to fit.

    After reaching exit code 0 via a project drop:
    - Check if the freed space can be used to strengthen remaining projects.
    - For each remaining selected project, scan its analysis.md for talking points or
      ATS keywords not yet represented in the current bullets.
    - Identify the 1-2 strongest unused talking points most relevant to this JD.
    - Propose adding one new bullet (or improving the weakest existing one) to a project
      that has room. Show the candidate bullet(s) to the user.
    - If the user approves, add the bullet to the context YAML and re-render.
      If adding causes overflow again, discard and report the final PDF as-is.
    - If the user declines, report the final PDF as-is.
13. Report where the PDF landed
