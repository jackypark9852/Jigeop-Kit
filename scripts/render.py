#!/usr/bin/env python3
"""Render a LaTeX template from a YAML context file and compile to PDF.

Usage:
    python scripts/render.py resume       context.yaml [--output output/resumes/]
    python scripts/render.py cover_letter context.yaml [--output output/cover_letters/]

Claude Code calls this after writing a tailored context YAML.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

# Repo root is one level up from scripts/
REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT))
from templates.jinja_env import get_env

TEMPLATE_MAP = {
    "resume": "resume.tex.j2",
    "cover_letter": "cover_letter.tex.j2",
}

# PDF filename per doc type (lives inside output/<job-slug>/)
DOC_FILENAME = {
    "resume": "resume.pdf",
    "cover_letter": "cover-letter.pdf",
}


def render(doc_type: str, context_path: Path, output_dir: Path | None) -> tuple[Path, int]:
    """Render template → LaTeX → PDF. Returns (path to PDF, page count).

    Output layout (default):
        output/<output_filename>/resume.pdf
        output/<output_filename>/cover-letter.pdf

    Pass output_dir to override the directory.
    """
    template_name = TEMPLATE_MAP[doc_type]
    env = get_env()
    template = env.get_template(template_name)

    context = yaml.safe_load(context_path.read_text(encoding="utf-8"))
    tex_source = template.render(**context)

    # Derive output path from context's output_filename (job slug)
    slug = context.get("output_filename") or context_path.stem
    if output_dir is None:
        output_dir = REPO_ROOT / "output" / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = DOC_FILENAME[doc_type]          # e.g. "resume.pdf"
    pdf_dest = output_dir / stem

    # Save .tex source alongside PDF for manual editing
    tex_dest = output_dir / stem.replace(".pdf", ".tex")
    tex_dest.write_text(tex_source, encoding="utf-8")
    print(f"TeX written to: {tex_dest}")

    # Compile in a temp dir so pdflatex aux files don't pollute the repo
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tex_file = tmp_path / f"{stem}.tex"
        tex_file.write_text(tex_source, encoding="utf-8")

        pdflatex = shutil.which("pdflatex")
        if not pdflatex:
            # Check common MiKTeX install locations on Windows
            for candidate in [
                Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe",
                Path("C:/Program Files/MiKTeX/miktex/bin/x64/pdflatex.exe"),
            ]:
                if candidate.exists():
                    pdflatex = str(candidate)
                    break
        if not pdflatex:
            print("ERROR: pdflatex not found. Install TeX Live or MiKTeX.", file=sys.stderr)
            sys.exit(1)

        cmd = [
            pdflatex,
            "-interaction=nonstopmode",
            "-output-directory", tmp,
            str(tex_file),
        ]

        # Run twice so references / page numbers settle
        for run in range(2):
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"pdflatex error (run {run + 1}):", file=sys.stderr)
                print(result.stdout[-3000:], file=sys.stderr)
                sys.exit(1)

        # Parse page count from pdflatex log.
        # pdflatex may line-wrap the "Output written on ... (N pages, ...)"
        # message, so search for just the "(N page" part.
        pages = 1  # fallback
        m = re.search(r"\((\d+) pages?,", result.stdout)
        if m:
            pages = int(m.group(1))

        pdf_src = tmp_path / f"{stem}.pdf"
        shutil.copy2(pdf_src, pdf_dest)

    print(f"PDF written to: {pdf_dest}")
    if pages > 1:
        print(f"WARNING: {doc_type} is {pages} pages (target: 1)")
    return pdf_dest, pages


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a job application document to PDF")
    parser.add_argument("doc_type", choices=list(TEMPLATE_MAP), help="Document type")
    parser.add_argument("context", type=Path, help="Path to YAML context file")
    parser.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Override output directory (default: output/<job-slug>/)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=None,
        help="Maximum allowed pages. Exit code 2 if exceeded."
    )
    args = parser.parse_args()

    if not args.context.exists():
        print(f"ERROR: context file not found: {args.context}", file=sys.stderr)
        sys.exit(1)

    _pdf_path, pages = render(args.doc_type, args.context, args.output)

    if args.max_pages is not None and pages > args.max_pages:
        print(
            f"OVERFLOW: {pages} pages exceeds --max-pages {args.max_pages}",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
