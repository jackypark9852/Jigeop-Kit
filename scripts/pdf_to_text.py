#!/usr/bin/env python3
"""Convert PDF files to plain-text sidecars for token-efficient reading.

Usage:
    python scripts/pdf_to_text.py profile/raw/resumes/resume.pdf
    python scripts/pdf_to_text.py profile/raw/resumes/        # convert all PDFs in dir
    python scripts/pdf_to_text.py profile/raw/resumes/ --force  # re-extract even if .txt exists

Output: writes <name>.txt alongside each <name>.pdf.
Claude Code reads the .txt instead of the PDF directly.
"""

import argparse
import sys
from pathlib import Path


def convert(pdf_path: Path, force: bool = False) -> None:
    txt_path = pdf_path.with_suffix(".txt")

    if txt_path.exists() and not force:
        print(f"skipped (exists): {txt_path}")
        return

    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("ERROR: pymupdf not installed. Run: pip install pymupdf", file=sys.stderr)
        sys.exit(1)

    doc = fitz.open(str(pdf_path))
    text = "\n\n".join(page.get_text() for page in doc)
    doc.close()

    txt_path.write_text(text, encoding="utf-8")
    print(f"converted: {txt_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert PDFs to .txt sidecars")
    parser.add_argument("source", type=Path, help="PDF file or directory of PDFs")
    parser.add_argument("--force", action="store_true", help="Re-extract even if .txt already exists")
    args = parser.parse_args()

    source: Path = args.source

    if source.is_dir():
        pdfs = sorted(source.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs found in {source}")
            return
        for pdf in pdfs:
            convert(pdf, force=args.force)
    elif source.is_file() and source.suffix.lower() == ".pdf":
        convert(source, force=args.force)
    else:
        print(f"ERROR: expected a .pdf file or directory, got: {source}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
