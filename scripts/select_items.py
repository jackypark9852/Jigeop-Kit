#!/usr/bin/env python3
"""Interactive multi-select for resume projects, experience, and extra keywords.

Usage:
    python scripts/select_items.py proposal.yaml -o selection.yaml

Reads a proposal YAML with pre-checked recommendations, launches an
interactive checkbox picker in the terminal, and writes the final
selection to a file.

Proposal YAML schema:
    experience:
      - name: "Alibaba Group"
        reason: "Unreal Engine rendering"
        checked: true
    projects:
      - name: "CUDA Path Tracer"
        reason: "matches GPU computing requirement"
        checked: true
    keywords:           # optional — borderline ATS keywords needing user approval
      - name: "OpenXR"
        reason: "JD requires XR dev; in skills_pool but no XR project yet"
        checked: true

Output YAML schema (only selected items):
    experience:
      - "Alibaba Group"
    projects:
      - "CUDA Path Tracer"
      - "Forward Plus and Clustered Deferred Renderer"
    keywords:           # omitted if no keywords section in proposal
      - "OpenXR"
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

import yaml


def run_checkbox(title: str, items: list[dict]) -> list[str]:
    """Launch a checkbox prompt. Returns list of selected item names."""
    import questionary

    choices = [
        questionary.Choice(
            title=f"{item['name']} — {item.get('reason', '')}",
            value=item["name"],
            checked=item.get("checked", False),
        )
        for item in items
    ]
    selected = questionary.checkbox(
        title,
        choices=choices,
        instruction="(arrow keys move, Space toggles, Enter confirms)",
    ).ask()

    if selected is None:
        print("Selection cancelled.", file=sys.stderr)
        sys.exit(1)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive resume item selector")
    parser.add_argument("proposal", type=Path, help="Path to proposal YAML")
    parser.add_argument(
        "--output", "-o", type=Path, required=True,
        help="Write selection YAML to this file",
    )
    parser.add_argument(
        "--spawn", action="store_true",
        help="Re-launch this script in a new console window (used internally)",
    )
    args = parser.parse_args()

    # If not already in a real console and on Windows, re-launch in a new window
    if (
        not args.spawn
        and platform.system() == "Windows"
        and not _has_console()
    ):
        script = Path(__file__).resolve()
        cmd = [
            sys.executable, str(script),
            str(args.proposal.resolve()),
            "-o", str(args.output.resolve()),
            "--spawn",
        ]
        # Launch in a new cmd.exe window and wait for it to finish
        subprocess.run(
            ["cmd.exe", "/c", "start", "/wait", "Select Resume Items",
             sys.executable, str(script),
             str(args.proposal.resolve()),
             "-o", str(args.output.resolve()),
             "--spawn"],
        )
        if args.output.exists():
            print(f"Selection written to: {args.output}", file=sys.stderr)
        else:
            print("ERROR: selection was cancelled or failed.", file=sys.stderr)
            sys.exit(1)
        return

    proposal = yaml.safe_load(args.proposal.read_text(encoding="utf-8"))
    result = {}

    if "experience" in proposal and proposal["experience"]:
        result["experience"] = run_checkbox(
            "Select experience entries:", proposal["experience"]
        )

    if "projects" in proposal and proposal["projects"]:
        result["projects"] = run_checkbox(
            "Select projects:", proposal["projects"]
        )

    if "keywords" in proposal and proposal["keywords"]:
        result["keywords"] = run_checkbox(
            "Approve extra skills keywords (in pool, match JD, not directly backed by selected projects):",
            proposal["keywords"]
        )

    output_text = yaml.dump(result, default_flow_style=False, allow_unicode=True)
    args.output.write_text(output_text, encoding="utf-8")
    print(f"Selection written to: {args.output}")


def _has_console() -> bool:
    """Check if we're running in a real Windows console."""
    if platform.system() != "Windows":
        return True
    try:
        # If TERM is set to xterm-*, we're likely in Git Bash / non-console
        term = os.environ.get("TERM", "")
        if "xterm" in term:
            return False
        return True
    except Exception:
        return False


if __name__ == "__main__":
    main()
