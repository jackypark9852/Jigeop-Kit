Run Workflow 4 (Full Application Package) from CLAUDE.md for the following job: $ARGUMENTS

If $ARGUMENTS is a file path (e.g. jobs/stripe-sre.md), read that file for the job description.
If $ARGUMENTS is a URL, fetch the page content and extract the job description from it.
If $ARGUMENTS is empty, ask which job to apply for before proceeding.

This command generates both a tailored resume and a cover letter for the same job.
Run them in sequence — the cover letter uses the resume output for context.

## Step 1: Tailor the resume

Follow the full `/tailor` workflow (all steps from tailor.md) for this job.
Wait until the resume PDF is successfully rendered before proceeding.

## Step 2: Write the cover letter

Follow the full `/cover-letter` workflow (all steps from cover-letter.md) for the same job.
The cover letter step will automatically read `output/<slug>/resume-context.yaml` from step 1
to use complementary angles — it won't repeat the same highlights already on the resume.

## Step 3: Report

Tell the user where both outputs landed:
- Resume: `output/<slug>/resume.pdf`
- Cover letter: `output/<slug>/cover-letter.pdf`
- Editable sources: `output/<slug>/resume.tex` and `output/<slug>/cover-letter.tex`
