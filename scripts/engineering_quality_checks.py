#!/usr/bin/env python3
"""Engineering quality gate for petaccess v0.1.0 (M1) — check implementations.

Enforces Global Engineering Instructions as an automated, non-blind gate.
Split from check_engineering_quality.py so every production file stays
<= 300 lines (the rules this gate enforces apply to the gate itself).

Every FAIL can be silenced ONLY through an explicit entry in
`scripts/gate_exemptions.json` that references a documented reason in
docs/audit/V010_TECH_DEBT_REGISTER.md — no path-based blanket ignores.

Pure stdlib; Python 3.11+.
"""

from __future__ import annotations

import ast
import fnmatch
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent  # monorepo root

EXEMPT_DIR_PARTS = ("node_modules", ".venv", "dist", "unpackage", "__pycache__")
GENERATED_PATTERNS = ("schema.d.ts", "openapi.json", ".d.ts")
WARN_SIZE, FAIL_SIZE = 250, 300
VUE_WARN, VUE_FAIL = 150, 200
FN_FAIL_LINES, CYCLO_WARN, CYCLO_FAIL = 60, 10, 15


def is_exempt(exemptions: list[dict], rule: str, root: Path, path: Path) -> bool:
    try:
        rel = str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        rel = str(path)  # root mismatch: fall back to absolute path match
    for ex in exemptions:
        if ex["rule"] != rule:
            continue
        if fnmatch.fnmatch(rel, ex["path"]) or fnmatch.fnmatch(str(path), ex["path"]):
            return True
    return False


def iter_py(path: Path) -> Iterable[Path]:
    paths = [path] if path.is_file() else sorted(path.rglob("*.py"))
    for p in paths:
        if any(part in EXEMPT_DIR_PARTS for part in p.parts):
            continue
        if "migrations" in p.parts:  # alembic revisions exempt by policy
            continue
        yield p


def iter_frontend(path: Path) -> Iterable[Path]:
    if path.is_file():
        if path.suffix in (".vue", ".uvue", ".ts"):
            yield path
        return
    files = sorted(path.rglob("*.vue")) + sorted(path.rglob("*.uvue")) + sorted(path.rglob("*.ts"))
    for p in files:
        if any(part in EXEMPT_DIR_PARTS for part in p.parts):
            continue
        if p.name.endswith(GENERATED_PATTERNS):
            continue
        yield p


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def check_size(exemptions: list[dict], py_roots: list[Path], ts_roots: list[Path]) -> list[dict]:
    out: list[dict] = []
    for root in py_roots:
        for p in iter_py(root):
            n = line_count(p)
            if n > FAIL_SIZE:
                out.append(
                    {
                        "rule": "file>300",
                        "path": str(p.relative_to(root)),
                        "severity": "FAIL",
                        "detail": str(n),
                    }
                )
            elif n > WARN_SIZE:
                out.append(
                    {
                        "rule": "file>250",
                        "path": str(p.relative_to(root)),
                        "severity": "WARN",
                        "detail": str(n),
                    }
                )
    for root in ts_roots:
        for p in iter_frontend(root):
            n = line_count(p)
            vue = p.suffix in (".vue", ".uvue")
            rule, limit = ("vue>200", VUE_FAIL) if vue else ("ts>300", FAIL_SIZE)
            if n > limit:
                out.append(
                    {
                        "rule": rule,
                        "path": str(p.relative_to(root)),
                        "severity": "FAIL",
                        "detail": str(n),
                    }
                )
            elif vue and n > VUE_WARN:
                out.append(
                    {
                        "rule": "vue>150",
                        "path": str(p.relative_to(root)),
                        "severity": "WARN",
                        "detail": str(n),
                    }
                )
    root = REPO_ROOT
    return [v for v in out if not is_exempt(exemptions, v["rule"], root, root / v["path"])]


def py_metrics(path: Path) -> list[dict]:
    """Per-function body-size and cyclomatic complexity (McCabe over AST)."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    try:
        rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        rel = str(path)  # outside the repo (unit-test fixtures): absolute path
    out: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body_lines = (node.end_lineno or node.lineno) - node.lineno + 1
        cyclo = 1
        for c in ast.walk(node):
            if isinstance(
                c, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.Assert)
            ):
                cyclo += 1
            elif isinstance(c, ast.BoolOp):
                cyclo += len(c.values) - 1
            elif isinstance(c, ast.comprehension):
                cyclo += 1
        kind = "async" if isinstance(node, ast.AsyncFunctionDef) else "fn"
        label = f"{path.name}:{kind}:{node.name}"
        if body_lines > FN_FAIL_LINES:
            out.append(
                {
                    "rule": "fn>60",
                    "path": rel,
                    "severity": "REVIEW",
                    "detail": f"{label} body={body_lines}L",
                }
            )
        if cyclo > CYCLO_FAIL:
            out.append(
                {
                    "rule": "cyclo>15",
                    "path": rel,
                    "severity": "REVIEW",
                    "detail": f"{label} cyclo={cyclo}",
                }
            )
        elif cyclo > CYCLO_WARN:
            out.append(
                {
                    "rule": "cyclo>10",
                    "path": rel,
                    "severity": "WARN",
                    "detail": f"{label} cyclo={cyclo}",
                }
            )
    return out


def check_functions(exemptions: list[dict], py_roots: list[Path]) -> list[dict]:
    out: list[dict] = []
    for r in py_roots:
        for p in iter_py(r):
            out.extend(py_metrics(p))
    return [
        v
        for v in out
        if not is_exempt(exemptions, v["rule"], REPO_ROOT, REPO_ROOT / v["path"].lstrip("/\\"))
    ]


def module_name(p: Path, root: Path) -> str:
    # Fully-qualified first-party module name under the given package root.
    # __init__.py maps to the package itself (app/models -> app.models).
    parts = list(p.relative_to(root).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return (root.name + "." + ".".join(parts)) if parts else root.name


def imports_of(p: Path) -> list[tuple[str, int]]:
    # First-party import specifiers of a file as (spec, level) pairs.
    # level == 0 -> absolute import (`from app.x import y`); level > 0 ->
    # relative import (`from .media import M` -> spec "media").
    # Imports guarded by `if TYPE_CHECKING:` are ignored: they are type-only
    # and cannot create an import-time runtime cycle.
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []

    def walk(node: ast.AST) -> list[tuple[str, int]]:
        out: list[tuple[str, int]] = []
        for child in ast.iter_child_nodes(node):
            if (
                isinstance(child, ast.If)
                and isinstance(child.test, ast.Name)
                and child.test.id == "TYPE_CHECKING"
            ):
                continue
            if isinstance(child, ast.Import):
                out.extend((a.name, 0) for a in child.names)
            elif isinstance(child, ast.ImportFrom):
                out.append((child.module or ".", child.level))
            out.extend(walk(child))
        return out

    return walk(tree)


def _resolve_targets(m: str, spec: str, level: int, names: set[str]) -> list[str]:
    # Resolve an import to fully-qualified module names. level > 0: relative
    # import (parent of m + spec). level == 0: absolute import, or a bare
    # sibling (`import b`) resolved as parent.b for the fixture namespace.
    if spec == ".":
        return []
    if level > 0:
        parent = m.rsplit(".", 1)[0] if "." in m else m
        target = spec if spec.startswith(".") else parent + "." + spec
        target = target.lstrip(".")
        return [target] if target in names else []
    if spec in names:
        return [spec]
    parent = m.rsplit(".", 1)[0] if "." in m else m
    sibling = parent + "." + spec
    return [sibling] if sibling in names else []


def dependency_cycles(py_roots: list[Path]) -> list[str]:
    # DFS over first-party imports; report every shortest-path cycle.
    graph: dict[str, list[str]] = defaultdict(list)
    fq: dict[Path, str] = {}
    for root in py_roots:
        for p in iter_py(root):
            fq[p] = module_name(p, root)
            graph[fq[p]] = []
    names = set(fq.values())
    for p, m in fq.items():
        for spec, level in imports_of(p):
            targets = _resolve_targets(m, spec, level, names)
            for target in targets:
                for candidate in fq.values():
                    if candidate == m:
                        continue
                    if candidate == target or candidate.startswith(target + "."):
                        graph[m].append(candidate)
    cycles: list[str] = []
    state: dict[str, int] = {}
    stack: list[str] = []

    def dfs(n: str) -> None:
        state[n] = 1
        stack.append(n)
        for nxt in sorted(dict.fromkeys(graph[n])):
            if nxt not in graph:
                continue
            if state.get(nxt) == 1:
                i = stack.index(nxt)
                cycles.append(" -> ".join(stack[i:] + [nxt]))
            elif state.get(nxt, 0) == 0:
                dfs(nxt)
        stack.pop()
        state[n] = 2

    for n in sorted(graph):
        if state.get(n, 0) == 0:
            dfs(n)
    return sorted(set(cycles))
