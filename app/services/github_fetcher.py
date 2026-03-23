"""
GitHub API client — fetches repository file tree and individual file contents
using raw requests calls (no PyGithub dependency).
"""

import base64
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── File-filter rules ────────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".txt", ".json",
    ".yaml", ".yml", ".html", ".css", ".java", ".go", ".rs",
    ".cpp", ".c", ".env.example",
}

SKIP_DIRS = {
    "node_modules/", ".git/", "dist/", "build/", "__pycache__/",
    ".next/", "venv/", "env/", ".venv/",
}

MAX_FILE_SIZE = 100 * 1024  # 100 KB


def _headers(token: Optional[str] = None) -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _should_include(path: str) -> bool:
    """Return True if the file path passes all filter rules."""
    for skip in SKIP_DIRS:
        if skip in path:
            return False
    # Check extension
    dot = path.rfind(".")
    if dot == -1:
        return False
    ext = path[dot:].lower()
    return ext in ALLOWED_EXTENSIONS


# ── Public API ───────────────────────────────────────────────────────────────


def get_repo_tree(
    owner: str, repo: str, token: Optional[str] = None
) -> list[str]:
    """
    Fetch the full recursive file tree of a GitHub repository.
    Returns a filtered list of file paths.
    """
    # 1. Get repo details to find the default branch
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    repo_resp = requests.get(repo_url, headers=_headers(token), timeout=30)

    if repo_resp.status_code == 404:
        raise ValueError(
            f"Repository '{owner}/{repo}' not found. "
            "If it's private, provide a Personal Access Token."
        )
    if repo_resp.status_code == 401:
        raise ValueError("Invalid GitHub token. Please check and try again.")
    if repo_resp.status_code == 403:
        raise ValueError(
            "GitHub API rate limit exceeded. "
            "Provide a Personal Access Token to increase the limit."
        )
    repo_resp.raise_for_status()

    default_branch = repo_resp.json().get("default_branch", "main")

    # 2. Fetch the file tree
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
    tree_resp = requests.get(tree_url, headers=_headers(token), timeout=30)
    tree_resp.raise_for_status()

    data = tree_resp.json()
    tree = data.get("tree", [])

    paths: list[str] = []
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item["path"]
        size = item.get("size", 0)
        if size > MAX_FILE_SIZE:
            continue
        if _should_include(path):
            paths.append(path)

    return paths


def get_file_content(
    owner: str,
    repo: str,
    path: str,
    token: Optional[str] = None,
) -> Optional[str]:
    """
    Fetch and base64-decode a single file from a GitHub repository.
    Returns the decoded text content, or None if the file is binary / unreadable.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=_headers(token), timeout=30)

    if resp.status_code != 200:
        logger.warning("Failed to fetch %s (HTTP %s)", path, resp.status_code)
        return None

    data = resp.json()
    content_b64 = data.get("content")
    if not content_b64:
        return None

    try:
        return base64.b64decode(content_b64).decode("utf-8")
    except (UnicodeDecodeError, ValueError):
        # Binary file — skip silently
        return None
