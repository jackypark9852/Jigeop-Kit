#!/usr/bin/env python3
"""Interactive multi-select for proposal items (resume, cover letter, etc.).

Usage:
    python scripts/select_items.py proposal.yaml -o selection.yaml

Reads a proposal YAML with pre-checked recommendations, launches an
interactive checkbox picker in the terminal, and writes the final
selection to a file.

Each top-level key in the proposal maps to a list of items with
{name, reason, checked} fields. The picker handles any section name.

Example proposal (resume):
    experience:
      - name: "Alibaba Group"
        reason: "Unreal Engine rendering"
        checked: true
    projects:
      - name: "CUDA Path Tracer"
        reason: "matches GPU computing requirement"
        checked: true
    keywords:
      - name: "OpenXR"
        reason: "JD requires XR dev; in skills_pool but no XR project yet"
        checked: true

Example proposal (cover letter):
    hooks:
      - name: "Achievement: 131× BVH speedup"
        reason: "Strong technical hook for GPU role"
        checked: true
    achievements:
      - name: "CUDA Path Tracer — 131× BVH speedup"
        reason: "Core GPU rendering achievement"
        checked: true
    company_angles:
      - name: "Their engineering blog on ray tracing"
        reason: "Direct technical overlap"
        checked: true

Output YAML (only selected item names per section):
    experience:
      - "Alibaba Group"
    projects:
      - "CUDA Path Tracer"
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
    parser = argparse.ArgumentParser(description="Interactive proposal item selector")
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
            ["cmd.exe", "/c", "start", "/wait", "Select Items",
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

    SECTION_PROMPTS = {
        "experience": "Select experience entries to include:",
        "projects": "Select projects to include:",
        "keywords": "Approve extra ATS keywords (in pool, match JD, not backed by selected projects):",
        "hooks": "Choose your opening hook approach (select 1):",
        "achievements": "Select achievements to highlight in cover letter (select 1-2):",
        "company_angles": "Select company-specific angles to reference (select 1):",
    }

    for key, items in proposal.items():
        if isinstance(items, list) and items and isinstance(items[0], dict):
            prompt = SECTION_PROMPTS.get(key, f"Select {key.replace('_', ' ')}:")
            result[key] = run_checkbox(prompt, items)

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
