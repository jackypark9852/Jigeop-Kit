#!/usr/bin/env python3
"""Clone project repos from resume.yaml into profile/raw/projects/repos/.

Usage:
    python scripts/clone_repos.py                     # clone all repos with URLs
    python scripts/clone_repos.py --force             # re-clone everything
    python scripts/clone_repos.py cuda-path-tracer    # specific slugs only

Saves:
    profile/raw/projects/repos/<slug>/               -- cloned repo (depth=1)
    profile/raw/projects/repos/<slug>/jacky_commits.txt  -- for contrib repos only
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REPOS_DIR = REPO_ROOT / "profile" / "raw" / "projects" / "repos"
RESUME_YAML = REPO_ROOT / "profile" / "resume.yaml"
JACKY_EMAIL_PATTERNS = ["jackypark9852", "jacky"]  # git author patterns to try


def slug_from_url(url: str) -> str:
    """Convert a github.com URL to a filesystem slug."""
    url = url.strip().rstrip("/")
    # e.g. github.com/jackypark9852/CUDA-Path-Tracer -> cuda-path-tracer
    parts = url.split("/")
    repo_name = parts[-1] if parts else url
    return repo_name.lower().replace("_", "-")


def to_https_url(url: str) -> str:
    """Convert bare github.com/owner/repo to https://github.com/owner/repo.git"""
    url = url.strip()
    if url.startswith("https://"):
        return url if url.endswith(".git") else url + ".git"
    if url.startswith("github.com/"):
        return "https://" + url + (".git" if not url.endswith(".git") else "")
    return url


def extract_repos(resume: dict) -> list[dict]:
    """Extract all entries with github.com URLs from projects[] and contributions[]."""
    entries = []
    for section, is_contrib in [("projects", False), ("contributions", True)]:
        for item in resume.get(section, []):
            url = item.get("url", "")
            if "github.com" in url:
                entries.append({
                    "name": item.get("name", ""),
                    "slug": slug_from_url(url),
                    "url": to_https_url(url),
                    "is_contrib": is_contrib,
                })
    return entries


def clone_repo(slug: str, url: str, force: bool) -> bool:
    """Clone repo to REPOS_DIR/<slug>. Returns True if successful."""
    dest = REPOS_DIR / slug
    if dest.exists() and (dest / ".git").exists() and not force:
        print(f"  skip (exists): {slug}")
        return True
    if dest.exists() and force:
        shutil.rmtree(dest)
    print(f"  cloning: {slug}  ({url})")
    result = subprocess.run(
        ["git", "clone", "--depth=1", url, str(dest)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  [!] Failed to clone {slug}: {result.stderr.strip()}", file=sys.stderr)
        return False
    print(f"  ok: {slug}")
    return True


def save_jacky_commits(slug: str) -> None:
    """Save Jacky's commit history + touched files for a contrib repo."""
    dest = REPOS_DIR / slug
    if not dest.exists():
        return
    out_path = dest / "jacky_commits.txt"
    lines = []
    for author in JACKY_EMAIL_PATTERNS:
        result = subprocess.run(
            ["git", "-C", str(dest), "log",
             f"--author={author}",
             "--name-only",
             "--format=commit %cd  %s",
             "--date=short"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            lines.append(result.stdout.strip())
            break
    if lines:
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  saved: {slug}/jacky_commits.txt")
    else:
        print(f"  [!] No commits found for jackypark9852 in {slug}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Clone project repos from resume.yaml")
    parser.add_argument("slugs", nargs="*", help="Specific repo slugs to clone (default: all)")
    parser.add_argument("--force", action="store_true", help="Re-clone even if already present")
    args = parser.parse_args()

    resume = yaml.safe_load(RESUME_YAML.read_text(encoding="utf-8"))
    all_repos = extract_repos(resume)

    if args.slugs:
        requested = {s.lower() for s in args.slugs}
        repos = [r for r in all_repos if r["slug"] in requested]
        if not repos:
            print(f"No repos matched slugs: {args.slugs}", file=sys.stderr)
            print("Known slugs:", [r["slug"] for r in all_repos])
            sys.exit(1)
    else:
        repos = all_repos

    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Cloning {len(repos)} repos into {REPOS_DIR}\n")

    for repo in repos:
        ok = clone_repo(repo["slug"], repo["url"], args.force)
        if ok and repo["is_contrib"]:
            save_jacky_commits(repo["slug"])

    print(f"\nDone. Repos in: {REPOS_DIR}")
    print("Next: run project analysis agents to generate analysis.md per project.")


if __name__ == "__main__":
    main()
