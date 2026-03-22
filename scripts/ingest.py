#!/usr/bin/env python3
"""Extract structured text from raw source files to help populate profile/.

Usage:
    python scripts/ingest.py resume   profile/raw/resumes/resume.pdf
    python scripts/ingest.py writing  profile/raw/writing_samples/
    python scripts/ingest.py github   profile/raw/github/
    python scripts/ingest.py website  profile/raw/websites/mysite.html

Output goes to stdout — review it, then paste into the relevant profile file.

resume  → paste into profile/resume.yaml
writing → paste into profile/style.md
github  → paste skills/projects block into profile/resume.yaml
website → paste text into profile/style.md or resume.yaml as needed
"""

import argparse
import re
import sys
from pathlib import Path


# ── Resume ingest ─────────────────────────────────────────────────────────────

def ingest_resume(source: Path) -> None:
    """Extract text from a PDF resume and print a resume.yaml scaffold."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("ERROR: pymupdf not installed. Run: pip install pymupdf", file=sys.stderr)
        sys.exit(1)

    if not source.exists():
        print(f"ERROR: file not found: {source}", file=sys.stderr)
        sys.exit(1)

    # Reuse .txt sidecar if it exists — avoids re-extracting and saves tokens
    txt_sidecar = source.with_suffix(".txt")
    if txt_sidecar.exists():
        full_text = txt_sidecar.read_text(encoding="utf-8")
    else:
        doc = fitz.open(str(source))
        pages = [page.get_text() for page in doc]
        full_text = "\n".join(pages)
        doc.close()

    print("# ── Extracted from:", source.name, "────────────────────────────────────")
    print("# Review carefully — heuristic extraction is imperfect.")
    print("# Paste corrected content into profile/resume.yaml\n")
    print(_build_yaml_scaffold(full_text))


def _build_yaml_scaffold(text: str) -> str:
    """Very light heuristic: find section headings and bullets."""
    lines = [l.rstrip() for l in text.splitlines()]

    # Try to grab name (usually the first non-empty line)
    name = ""
    contact_lines = []
    for line in lines[:8]:
        if not line.strip():
            continue
        if not name:
            name = line.strip()
        elif re.search(r"@|linkedin|github|http|\+1|\(\d{3}\)", line, re.I):
            contact_lines.append(line.strip())

    body_lines = []
    for line in lines:
        if line.strip():
            body_lines.append(line)

    out = []
    out.append(f"name: {_q(name)}")
    out.append(f"email: {_q(_extract(contact_lines, r'[\\w.+-]+@[\\w.-]+'))}")
    out.append(f"phone: {_q(_extract(contact_lines, r'[\\+\\d][\\d\\s().\\-]{7,}'))}")
    out.append(f"location: \"\"")
    out.append(f"linkedin: {_q(_extract(contact_lines, r'linkedin\\.com/in/[\\w-]+'))}")
    out.append(f"github: {_q(_extract(contact_lines, r'github\\.com/[\\w-]+'))}")
    out.append(f"website: \"\"")
    out.append("")
    out.append("summary: |")
    out.append("  # TODO: fill in")
    out.append("")
    out.append("experience:")
    out.append("  # TODO: parse from text below")
    out.append("")
    out.append("education:")
    out.append("  # TODO: parse from text below")
    out.append("")
    out.append("skills:")
    out.append("  languages:  []")
    out.append("  frameworks: []")
    out.append("  tools:      []")
    out.append("  platforms:  []")
    out.append("")
    out.append("projects: []")
    out.append("certifications: []")
    out.append("")
    out.append("# ── Raw extracted text (for reference) ──────────────────────────")
    out.append("# Delete this section after filling in the fields above.")
    out.append("#")
    for line in body_lines[:120]:  # Show first 120 non-empty lines
        out.append(f"# {line}")

    return "\n".join(out)


def _q(s: str) -> str:
    return f'"{s}"' if s else '""'


def _extract(lines: list[str], pattern: str) -> str:
    for line in lines:
        m = re.search(pattern, line, re.I)
        if m:
            return m.group(0)
    return ""


# ── Writing samples ingest ────────────────────────────────────────────────────

def ingest_writing(source: Path) -> None:
    """Concatenate text files and print a style.md scaffold."""
    if source.is_dir():
        files = sorted(source.glob("*"))
        files = [f for f in files if f.is_file() and not f.name.startswith(".")]
    elif source.is_file():
        files = [source]
    else:
        print(f"ERROR: not found: {source}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print(f"No files found in {source}", file=sys.stderr)
        sys.exit(1)

    print("# Writing Style — extracted from raw samples")
    print("# Paste into profile/style.md and edit the Voice & Tone Notes section.\n")
    print("## Voice & Tone Notes\n")
    print("[Review the samples below and write a 2-3 sentence description of your voice here]\n")
    print("## Writing Samples\n")

    for i, f in enumerate(files, 1):
        try:
            if f.suffix.lower() == ".pdf":
                try:
                    import fitz
                    doc = fitz.open(str(f))
                    text = "\n".join(page.get_text() for page in doc)
                    doc.close()
                except ImportError:
                    text = "[PDF — install pymupdf to extract]"
            else:
                text = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            text = f"[Could not read: {e}]"

        print(f"### Sample {i} — {f.name}\n")
        # Print up to 60 lines per sample
        for line in text.splitlines()[:60]:
            print(line)
        if len(text.splitlines()) > 60:
            print(f"\n[... {len(text.splitlines()) - 60} more lines — paste the rest manually]")
        print()


# ── GitHub ingest ─────────────────────────────────────────────────────────────

def ingest_github(source: Path) -> None:
    """Extract project and skill info from GitHub text exports."""
    if source.is_dir():
        files = sorted(source.glob("*"))
        files = [f for f in files if f.is_file() and not f.name.startswith(".")]
    elif source.is_file():
        files = [source]
    else:
        print(f"ERROR: not found: {source}", file=sys.stderr)
        sys.exit(1)

    print("# GitHub profile extract")
    print("# Paste relevant projects/skills into profile/resume.yaml\n")

    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"# Could not read {f.name}: {e}")
            continue

        print(f"## {f.name}\n")
        print(text[:3000])
        if len(text) > 3000:
            print(f"[... truncated — see {f} for full content]")
        print()

    print("\n# ── Suggested projects block for resume.yaml ──────────────────")
    print("projects:")
    print("  - name: \"\"")
    print("    description: \"\"")
    print("    tech: \"\"")
    print("    url: \"\"")


# ── Website ingest ────────────────────────────────────────────────────────────

def ingest_website(source: Path) -> None:
    """Strip HTML and extract readable text from a saved website file."""
    if not source.exists():
        print(f"ERROR: not found: {source}", file=sys.stderr)
        sys.exit(1)

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("ERROR: beautifulsoup4 not installed. Run: pip install beautifulsoup4", file=sys.stderr)
        sys.exit(1)

    html = source.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style
    for tag in soup(["script", "style", "nav", "footer", "head"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    print(f"# Website extract — {source.name}")
    print("# Use for style.md (voice) or resume.yaml (bio/projects)\n")
    for line in lines[:150]:
        print(line)
    if len(lines) > 150:
        print(f"\n[... {len(lines) - 150} more lines]")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Extract text from raw sources into profile files")
    parser.add_argument(
        "source_type",
        choices=["resume", "writing", "github", "website"],
        help="Type of source to ingest",
    )
    parser.add_argument("source", type=Path, help="File or directory to ingest")
    args = parser.parse_args()

    dispatch = {
        "resume": ingest_resume,
        "writing": ingest_writing,
        "github": ingest_github,
        "website": ingest_website,
    }
    dispatch[args.source_type](args.source)


if __name__ == "__main__":
    main()
