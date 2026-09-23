#!/usr/bin/env python3
"""Engineering quality gate (M1) — content-scan checks: type escapes, TODO, colors.

Split from engineering_quality_checks.py so every production file (including
the gate itself) stays <= 300 lines. Imports shared iterators/exemptions from
engineering_quality_checks.

Every FAIL can be silenced ONLY through an explicit entry in
`scripts/gate_exemptions.json` that references a documented reason in
docs/audit/V010_TECH_DEBT_REGISTER.md — no path-based blanket ignores.

Pure stdlib; Python 3.11+.
"""

from __future__ import annotations

import re
from pathlib import Path

from engineering_quality_checks import REPO_ROOT, is_exempt, iter_frontend, iter_py

BARELY_TRACKED_TODO = re.compile(r"\b(TODO|FIXME|HACK|TEMP|XXX)\b(?!\s*\()")
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FUNC_COLOR = re.compile(r"\b(?:rgb|rgba|hsl|hsla)\([\d.,\s%]+\)")
PY_IGNORE = re.compile(r"#\s*(type:\s*ignore|noqa)")
JUSTIFIED = re.compile(r"#\s*(SAFETY|SECURITY|INVARIANT|PRIVACY|PROVIDER|COMPATIBILITY):")
ANY_USE = re.compile(r"\bAny\b")
CAST_USE = re.compile(r"\bcast\s*\(")
TS_ESCAPE = re.compile(
    r":\s*any\b|as\s*any\b|<any>|@ts-ignore|@ts-expect-error|\bany\b\[\]|\bany\s*\)"
)
TS_IGNORE = re.compile(r"@ts-ignore|@ts-expect-error")
TS_JUST = re.compile(r"//\s*(SAFETY|SECURITY|WHY|COMPAT|PROVIDER)")


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)  # outside the repo (unit-test fixtures): absolute path


def _py_lines(root: Path, path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def check_type_escapes(
    exemptions: list[dict], py_roots: list[Path], ts_roots: list[Path]
) -> list[dict]:
    """Report unjustified `type: ignore` / `noqa` / `cast(` / `Any` (Python)
    and `any` / `as any` / `@ts-ignore` (TS). Ats-ignore with a following WHY
    comment or any escape with an adjacent JUSTIFIED marker counts as justified."""
    out: list[dict] = []
    root = REPO_ROOT
    for r in py_roots:
        for p in iter_py(r):
            for idx, line in enumerate(_py_lines(root, p), 1):
                esc = PY_IGNORE.search(line) or CAST_USE.search(line)
                if (
                    esc
                    and not JUSTIFIED.search(line)
                    and not is_exempt(exemptions, "type-escape", root, p)
                ):
                    out.append(
                        {
                            "rule": "type-escape",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": f"{idx}: {line.strip()[:70]}",
                        }
                    )
                if ANY_USE.search(line) and not JUSTIFIED.search(line):
                    if line.lstrip().startswith(("from", "import")):
                        continue
                    if not is_exempt(exemptions, "type-escape", root, p):
                        out.append(
                            {
                                "rule": "type-escape",
                                "path": _rel(root, p),
                                "severity": "FAIL",
                                "detail": f"{idx}: Any usage",
                            }
                        )
    for r in ts_roots:
        for p in iter_frontend(r):
            if p.suffix not in (".ts", ".vue"):
                continue
            lines = _py_lines(root, p)
            for idx, line in enumerate(lines, 1):
                if line.lstrip().startswith(("//", "*")) or not TS_ESCAPE.search(line):
                    continue
                justified = bool(TS_IGNORE.search(line)) and (
                    idx < len(lines) and TS_JUST.search(lines[idx])
                )
                if not justified and not is_exempt(exemptions, "type-escape", root, p):
                    out.append(
                        {
                            "rule": "type-escape",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": f"{idx}: {line.strip()[:70]}",
                        }
                    )
    return out


def check_todos(exemptions: list[dict], py_roots: list[Path], ts_roots: list[Path]) -> list[dict]:
    """Bare TODO/FIXME/HACK/TEMP/XXX must be 0. Tracked `TODO(ID):` passes."""
    out: list[dict] = []
    root = REPO_ROOT
    for r in py_roots + ts_roots:
        iterf = iter_py if r in py_roots else iter_frontend
        for p in iterf(r):
            for idx, line in enumerate(_py_lines(root, p), 1):
                if BARELY_TRACKED_TODO.search(line) and not is_exempt(exemptions, "todo", root, p):
                    out.append(
                        {
                            "rule": "todo",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": f"{idx}: {line.strip()[:70]}",
                        }
                    )
    return out


def check_ts_colors(exemptions: list[dict], ts_roots: list[Path]) -> list[dict]:
    """Hardcoded hex/rgb/hsl colors outside design tokens must be 0."""
    out: list[dict] = []
    root = REPO_ROOT
    for r in ts_roots:
        for p in iter_frontend(r):
            if p.name == "tokens.css" or "design-tokens" in p.parts:
                continue
            for idx, line in enumerate(_py_lines(root, p), 1):
                if not (HEX_COLOR.search(line) or FUNC_COLOR.search(line)):
                    continue
                if line.lstrip().startswith(("//", "*", "<!--")):
                    continue
                if not is_exempt(exemptions, "hardcoded-color", root, p):
                    out.append(
                        {
                            "rule": "hardcoded-color",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": f"{idx}: {line.strip()[:70]}",
                        }
                    )
    return out
