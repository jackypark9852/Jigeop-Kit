#!/usr/bin/env python3
"""Fetch GitHub profile data and save to profile/raw/github/ as readable files.

Usage:
    python scripts/fetch_github.py jackypark9852
    python scripts/fetch_github.py jackypark9852 --contrib rubenaryo/Cumulus tonytgrt/Umbra
    python scripts/fetch_github.py jackypark9852 --token ghp_xxx  # higher rate limit
    python scripts/fetch_github.py jackypark9852 --force          # re-fetch everything

Saves:
    profile/raw/github/profile.json                  -- user bio + stats
    profile/raw/github/repos.json                    -- all public repos
    profile/raw/github/readmes/<repo>.md             -- README per repo
    profile/raw/github/contrib_<owner>_<repo>.json   -- contrib repo metadata + commit list
    profile/raw/github/contrib_<owner>_<repo>_readme.md
    profile/raw/github/summary.md                    -- consolidated human-readable summary
"""

import argparse
import base64
import json
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

REPO_ROOT = Path(__file__).resolve().parent.parent
GITHUB_DIR = REPO_ROOT / "profile" / "raw" / "github"
API_BASE = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "jigeop-profile-fetcher/1.0",
}


def get(url: str, token: str = "") -> dict | list:
    """Make a GitHub API GET request, return parsed JSON."""
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=15) as resp:
            remaining = resp.getheader("X-RateLimit-Remaining", "?")
            if remaining != "?" and int(remaining) < 5:
                print(f"  [!] Rate limit low ({remaining} remaining) -- sleeping 10s")
                time.sleep(10)
            return json.loads(resp.read().decode())
    except HTTPError as e:
        if e.code == 404:
            return {}
        if e.code == 403:
            print(f"  [x] Rate limited or forbidden: {url}", file=sys.stderr)
            return {}
        raise
    except URLError as e:
        print(f"  [x]  Network error: {e}", file=sys.stderr)
        return {}


def save_json(path: Path, data: dict | list, force: bool) -> bool:
    """Save JSON to path. Returns True if written."""
    if path.exists() and not force:
        print(f"  skip (exists): {path.name}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  saved: {path.name}")
    return True


def save_text(path: Path, text: str, force: bool) -> bool:
    if path.exists() and not force:
        print(f"  skip (exists): {path.name}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  saved: {path.name}")
    return True


def fetch_readme(owner: str, repo: str, token: str) -> str:
    """Fetch README content for a repo, return as plain text."""
    data = get(f"{API_BASE}/repos/{owner}/{repo}/readme", token)
    if data and "content" in data:
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            pass
    return ""


def fetch_profile(username: str, token: str, force: bool) -> dict:
    print(f"\n[1/4] Fetching profile for {username}...")
    path = GITHUB_DIR / "profile.json"
    data = get(f"{API_BASE}/users/{username}", token)
    save_json(path, data, force)
    return data


def fetch_repos(username: str, token: str, force: bool) -> list:
    print(f"\n[2/4] Fetching repos...")
    path = GITHUB_DIR / "repos.json"

    all_repos = []
    page = 1
    while True:
        page_data = get(f"{API_BASE}/users/{username}/repos?sort=updated&per_page=100&page={page}", token)
        if not page_data:
            break
        all_repos.extend(page_data)
        if len(page_data) < 100:
            break
        page += 1
        time.sleep(0.3)

    save_json(path, all_repos, force)
    print(f"  {len(all_repos)} repos found")
    return all_repos


def fetch_readmes(username: str, repos: list, token: str, force: bool) -> dict[str, str]:
    print(f"\n[3/4] Fetching READMEs...")
    readmes_dir = GITHUB_DIR / "readmes"
    readmes_dir.mkdir(parents=True, exist_ok=True)

    readmes = {}
    # Only fetch for repos that seem substantial (not forks with no description, not tiny)
    notable = [r for r in repos if r.get("owner", {}).get("login") == username]

    for repo in notable:
        name = repo["name"]
        path = readmes_dir / f"{name}.md"
        if path.exists() and not force:
            print(f"  skip (exists): {name}.md")
            readmes[name] = path.read_text(encoding="utf-8")
            continue
        text = fetch_readme(username, name, token)
        if text:
            save_text(path, text, force=True)
            readmes[name] = text
        time.sleep(0.2)

    return readmes


def fetch_contrib(username: str, owner_repo: str, token: str, force: bool) -> dict:
    owner, repo = owner_repo.split("/", 1)
    slug = f"{owner}_{repo}"
    print(f"\n  -> Contrib repo: {owner_repo}")

    # Repo metadata
    meta_path = GITHUB_DIR / f"contrib_{slug}.json"
    meta = get(f"{API_BASE}/repos/{owner}/{repo}", token)
    time.sleep(0.3)

    # Jacky's commits
    commits = []
    page = 1
    while True:
        page_data = get(
            f"{API_BASE}/repos/{owner}/{repo}/commits?author={username}&per_page=100&page={page}",
            token,
        )
        if not page_data or not isinstance(page_data, list):
            break
        commits.extend(page_data)
        if len(page_data) < 100:
            break
        page += 1
        time.sleep(0.3)

    # Contributors
    contributors = get(f"{API_BASE}/repos/{owner}/{repo}/contributors?per_page=50", token)
    time.sleep(0.3)

    combined = {
        "repo": meta,
        "jacky_commits": [
            {
                "sha": c["sha"][:8],
                "message": c["commit"]["message"].split("\n")[0],
                "date": c["commit"]["author"]["date"],
            }
            for c in commits
            if isinstance(c, dict) and "commit" in c
        ],
        "contributors": [
            {"login": c.get("login"), "contributions": c.get("contributions")}
            for c in (contributors if isinstance(contributors, list) else [])
        ],
    }
    save_json(meta_path, combined, force)

    # README
    readme_path = GITHUB_DIR / f"contrib_{slug}_readme.md"
    readme = fetch_readme(owner, repo, token)
    if readme:
        save_text(readme_path, readme, force)

    return combined


def build_summary(username: str, profile: dict, repos: list, readmes: dict, contribs: dict[str, dict]) -> str:
    """Build a consolidated summary.md for Claude Code to read."""
    lines = []

    # Profile
    lines += [
        f"# GitHub Summary -- {username}",
        "",
        f"**Name:** {profile.get('name', username)}",
        f"**Bio:** {profile.get('bio', '')}",
        f"**Location:** {profile.get('location', '')}",
        f"**Company:** {profile.get('company', '')}",
        f"**Website:** {profile.get('blog', '')}",
        f"**Public repos:** {profile.get('public_repos', '?')}",
        f"**Followers:** {profile.get('followers', '?')}",
        "",
    ]

    # Owned repos summary
    owned = [r for r in repos if not r.get("fork")]
    lines += ["## Owned Repositories", ""]
    for r in sorted(owned, key=lambda x: x.get("updated_at", ""), reverse=True):
        name = r["name"]
        desc = r.get("description") or ""
        lang = r.get("language") or ""
        stars = r.get("stargazers_count", 0)
        updated = (r.get("updated_at") or "")[:10]
        lines.append(f"### {name}")
        if desc:
            lines.append(f"**Description:** {desc}")
        if lang:
            lines.append(f"**Language:** {lang}")
        if stars:
            lines.append(f"**Stars:** {stars}")
        lines.append(f"**Updated:** {updated}")
        # Include README snippet if available
        if name in readmes and readmes[name]:
            snippet = readmes[name][:1500].strip()
            lines += ["", "**README excerpt:**", "```", snippet, "```"]
        lines.append("")

    # Contributions
    if contribs:
        lines += ["## External Contributions", ""]
        for owner_repo, data in contribs.items():
            repo_meta = data.get("repo", {})
            commits = data.get("jacky_commits", [])
            contributors = data.get("contributors", [])
            jacky_contrib = next((c for c in contributors if c.get("login") == username), {})
            total_commits = jacky_contrib.get("contributions", len(commits))

            lines += [
                f"### {owner_repo}",
                f"**Description:** {repo_meta.get('description', '')}",
                f"**Language:** {repo_meta.get('language', '')}",
                f"**Stars:** {repo_meta.get('stargazers_count', 0)}",
                f"**Jacky's commits:** {total_commits}",
                "",
                "**Commit history:**",
            ]
            for c in commits[:30]:
                lines.append(f"- `{c['date'][:10]}` {c['message']}")
            lines.append("")

            readme_path = GITHUB_DIR / f"contrib_{owner_repo.replace('/', '_')}_readme.md"
            if readme_path.exists():
                snippet = readme_path.read_text(encoding="utf-8")[:2000].strip()
                lines += ["**README excerpt:**", "```", snippet, "```", ""]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch GitHub data into profile/raw/github/")
    parser.add_argument("username", help="GitHub username")
    parser.add_argument("--contrib", nargs="*", default=[], metavar="OWNER/REPO",
                        help="External repos to include contribution data for")
    parser.add_argument("--token", default="", help="GitHub personal access token (optional)")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if files exist")
    args = parser.parse_args()

    GITHUB_DIR.mkdir(parents=True, exist_ok=True)

    profile = fetch_profile(args.username, args.token, args.force)
    repos = fetch_repos(args.username, args.token, args.force)
    readmes = fetch_readmes(args.username, repos, args.token, args.force)

    print(f"\n[4/4] Fetching contrib repos...")
    contribs = {}
    for owner_repo in args.contrib:
        if "/" not in owner_repo:
            print(f"  [x]  Invalid format (expected owner/repo): {owner_repo}", file=sys.stderr)
            continue
        contribs[owner_repo] = fetch_contrib(args.username, owner_repo, args.token, args.force)
        time.sleep(0.5)

    # Build and save summary
    summary = build_summary(args.username, profile, repos, readmes, contribs)
    summary_path = GITHUB_DIR / "summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    print(f"\n  saved: summary.md ({len(summary):,} chars)")
    print(f"\nDone. Files in: {GITHUB_DIR}")
    print("Claude Code reads: profile/raw/github/summary.md")


if __name__ == "__main__":
    main()
