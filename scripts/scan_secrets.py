#!/usr/bin/env python3
"""Secret scanner for petaccess v0.1.0 (A7 / G2).

Scans the worktree (git-tracked files) and the full git history for high-
signal secret patterns. Values carrying explicit dev/demo markers
(`dev_only`, `example`, `changeme`, `placeholder`) are treated as benign.

Only reports; never writes. Exit 0 = no hits, 1 = hits found, 2 = internal error.

Usage:
    uv run python scripts/scan_secrets.py            # worktree + history
    uv run python scripts/scan_secrets.py --worktree # current tree only
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = (
    ".git",
    "node_modules",
    ".venv",
    "dist",
    "unpackage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "target",
    # The scanner's own unit test deliberately embeds fake secrets to prove
    # each pattern fires. Scanning it would always report them — excluding
    # the fixture keeps the gate meaningful (see tests/unit/test_scan_secrets.py).
    "test_scan_secrets.py",
)

DEV_MARKERS = (
    "dev_only",
    "dev-only",
    "example",
    "changeme",
    "change_me",
    "change-me",
    "placeholder",
    "your_",
    "your-",
    "xxx",
    "dummy",
    "not a real",
    "REPLACE_ME",
    "user:pw",
    "u:p@",
    "petaccess:x@",
    "{user}",
    "{password}",
    "***",
)

AWS_KEY = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
GITHUB_TOKEN = re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b")
PRIVATE_KEY_BLOCK = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
JWT_HINT = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.\w+\.[A-Za-z0-9_-]{10,}")
GENERIC_SECRET = re.compile(
    r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?key|password|passwd|jwt[_-]?secret|"
    r"client[_-]?secret)\b\s*[=:]\s*['\"]?[A-Za-z0-9_\-./+]{16,}"
)
DATABASE_URL_CRED = re.compile(r"postgres(?:ql)?\+?\w*://[^:/\s]+:[^@/\s]+@")
NASA_PATTERN = re.compile(r"NAS[A-Z]{3}KEY")

HIGH_SIGNAL = {
    "AWS access key",
    "GitHub token",
    "private key block",
    "NASA API key",
}

PATTERNS = [
    ("AWS access key", AWS_KEY),
    ("GitHub token", GITHUB_TOKEN),
    ("private key block", PRIVATE_KEY_BLOCK),
    ("JWT in code", JWT_HINT),
    ("generic secret assignment", GENERIC_SECRET),
    ("DB URL with credentials", DATABASE_URL_CRED),
    ("NASA API key", NASA_PATTERN),
]


def is_dev_line(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in DEV_MARKERS)


def scan_text(text: str) -> list[tuple[str, int]]:
    """Return [(pattern_name, line_number)] hits for one text blob.

    Dev/demo markers suppress only low-signal patterns (JWT, generic secret,
    DB URL). High-signal patterns (AWS/GitHub/private-key/NASA) are always
    reported: an "example" AKIA key still must be seen by a human, and a
    dev-labelled real key must not disappear.
    """
    hits: list[tuple[str, int]] = []
    for idx, raw in enumerate(text.splitlines(), 1):
        for name, rx in PATTERNS:
            if not rx.search(raw):
                continue
            if name not in HIGH_SIGNAL and is_dev_line(raw):
                continue
            hits.append((name, idx))
    return hits


def iter_tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if out.returncode != 0:
        print(f"[scan_secrets] git ls-files failed: {out.stderr[:200]}", file=sys.stderr)
        return []
    files: list[Path] = []
    for rel in out.stdout.splitlines():
        p = ROOT / rel
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        if p.is_file() and p.suffix not in (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".ico",
            ".woff",
            ".woff2",
        ):
            files.append(p)
    return files


def scan_worktree() -> list[dict]:
    results: list[dict] = []
    for p in iter_tracked_files():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, line in scan_text(text):
            results.append(
                {
                    "kind": "worktree",
                    "file": str(p.relative_to(ROOT)),
                    "line": line,
                    "pattern": name,
                }
            )
    return results


def scan_history() -> list[dict]:
    results: list[dict] = []
    out = subprocess.run(
        ["git", "log", "--all", "--full-history", "-p", "--format=%H"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if out.returncode != 0:
        print(f"[scan_secrets] git log -p failed: {out.stderr[:200]}", file=sys.stderr)
        return []
    current_sha = ""
    current_file = ""
    line_no = 0
    for raw in out.stdout.splitlines():
        if raw.startswith("commit "):
            current_sha = raw.split()[1]
            continue
        if raw.startswith("+++ b/"):
            current_file = raw[6:]
            line_no = 0
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            line = raw[1:]
            line_no += 1
            # Skip the scanner's own fixture file (deliberate fake secrets)
            if any(part in SKIP_PARTS for part in current_file.split("/")):
                continue
            if is_dev_line(line):
                continue
            for name, rx in PATTERNS:
                if rx.search(line):
                    results.append(
                        {
                            "kind": "history",
                            "file": current_file,
                            "line": line_no,
                            "pattern": name,
                            "commit": current_sha[:10],
                            "sample": line.strip()[:110],
                        }
                    )
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="petaccess secret scanner (A7)")
    ap.add_argument("--worktree", action="store_true", help="scan worktree only")
    ap.add_argument("--history", action="store_true", help="scan git history only")
    args = ap.parse_args()

    findings: list[dict] = []
    if not args.history:
        findings += scan_worktree()
    if not args.worktree:
        findings += scan_history()

    dedup: set[str] = set()
    unique: list[dict] = []
    for f in findings:
        key = f"{f['kind']}|{f['file']}|{f['line']}|{f['pattern']}"
        if key in dedup:
            continue
        dedup.add(key)
        unique.append(f)

    for f in unique:
        where = f"commit {f.get('commit', '-')} " if f["kind"] == "history" else ""
        sample = f.get("sample", "")
        print(f"[{f['kind']}] {f['pattern']}: {f['file']}:{f['line']} {where}{sample}")
    print(f"secret scan: {len(unique)} finding(s)")
    return 1 if unique else 0


if __name__ == "__main__":
    sys.exit(main())
