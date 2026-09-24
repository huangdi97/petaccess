#!/usr/bin/env python3
"""Engineering quality gate (v0.2.0 M1) — silent-catch and magic-status scanner.

Two of the four Master Goal §40 gates missing from the M1 gate set:

* ``silent catch``: an except handler that swallows the error without logging,
  re-raising, or warnings is invisible in production. It must log at least a
  debug line (matching the existing pattern in providers/mock.py and
  core/observability.py) or explicitly re-raise / warn.
* ``magic status``: comparing a domain status against a bare string literal
  (``effect == "allowed"``) instead of the canonical StrEnum member
  (``RuleEffect.ALLOWED``) lets typos and drift creep in. Values already have
  StrEnums in app/models/enums.py; equality against a member is identical to
  equality against its string value, so the replacement is behavior-preserving.

Every FAIL can be silenced ONLY through an explicit entry in
`scripts/gate_exemptions.json` referencing a documented reason in
docs/audit/V010_TECH_DEBT_REGISTER.md — no path-based blanket ignores.

Pure stdlib; Python 3.11+.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from engineering_quality_checks import REPO_ROOT, is_exempt, iter_frontend, iter_py

#: Domain status words that must be compared through their StrEnum members.
STATUS_WORDS = frozenset(
    {
        "allowed",
        "prohibited",
        "conditional",
        "active",
        "inactive",
        "pending",
        "published",
        "draft",
        "confirmed",
        "rejected",
        "approved",
        "verified",
        "unverified",
        "observed",
        "closed",
        "open",
        "unknown",
    }
)

LOGGING_METHODS = frozenset(
    {"debug", "info", "warning", "error", "exception", "critical", "log", "warn", "getLogger"}
)
TS_CATCH = re.compile(r"\bcatch\b")
TS_LOG_CALL = re.compile(r"\.(?:error|warn|log|debug|info|trace)\(")
TS_SILENT_ONLY = re.compile(r"^(return null;|return undefined;|return \[\];|})$")


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)  # outside the repo (unit-test fixtures): absolute path


def _py_lines(root: Path, path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _ts_catch_body(lines: list[str], catch_idx: int) -> list[str]:
    """Return the body lines of the catch block starting at ``catch_idx``.

    Collects lines from the catch statement until the brace that opens the
    block is closed. Returns [] when the block cannot be located (e.g. a
    one-line ``catch { }`` with no body — nothing to inspect).
    """
    depth = 0
    started = False
    body: list[str] = []
    for ln in lines[catch_idx:]:
        depth += ln.count("{") - ln.count("}")
        if depth > 0:
            started = True
        if started:
            body.append(ln)
            if depth <= 0 and ln.strip().endswith("}"):
                break
    if not started:
        return []
    # drop the catch line itself and the closing "}"
    body = body[1:]
    if body and body[-1].strip() in ("}", "});"):
        body = body[:-1]
    return body


# --- silent catch ----------------------------------------------------------


def _silent_handler_body(handler: ast.ExceptHandler) -> bool:
    """True when every statement in the handler is a literal no-op.

    Allowed statements: ``pass``, ``...``, a bare ``return``, or a constant
    ``return [] | None | "" | {}``. Anything else (a computed fallback, a
    ``return call()``, an assignment) is treated as a deliberate response and
    is not a silent catch.
    """
    if not handler.body:
        return True

    def constant_return(value: ast.AST | None) -> bool:
        if value is None:
            return True
        if isinstance(value, ast.Constant):
            return value.value is None or value.value == ""
        if isinstance(value, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            return not value.elts and not getattr(value, "keys", None)
        return False

    for stmt in handler.body:
        if isinstance(stmt, ast.Pass):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
            if stmt.value.value is Ellipsis:
                continue
            return False
        if isinstance(stmt, ast.Return):
            if constant_return(stmt.value):
                continue
            return False
        return False
    return True


def _has_logging_or_raise(handler: ast.ExceptHandler) -> bool:
    """Detect logging-family calls (logging.* / logger.nnn( / warnings.warn)
    or any raise anywhere in the handler subtree. A handler with either is
    never "silent"."""
    for node in ast.walk(handler):
        if isinstance(node, ast.Raise):
            return True
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                if func.attr in LOGGING_METHODS:
                    return True
            elif isinstance(func, ast.Name) and func.id in ("logging", "warnings"):
                return True
    return False


def check_silent_catches(
    exemptions: list[dict], py_roots: list[Path], ts_roots: list[Path]
) -> list[dict]:
    """Report except handlers that swallow errors with no log, warn, or raise.

    Python: AST-based, exact. TypeScript: line-based heuristic over catch
    blocks — the handler body must contain no `.error|warn|log(`/throw and
    nothing but `}`, `return null;`, `return undefined;`, `return [];`.
    """
    out: list[dict] = []
    root = REPO_ROOT
    for r in py_roots:
        for p in iter_py(r):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ExceptHandler):
                    continue
                if not _silent_handler_body(node) or _has_logging_or_raise(node):
                    continue
                if not is_exempt(exemptions, "silent-catch", root, p):
                    out.append(
                        {
                            "rule": "silent-catch",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": f"line {node.lineno}: silent except swallowed with "
                            "no log/raise",
                        }
                    )
    for r in ts_roots:
        for p in iter_frontend(r):
            if p.suffix not in (".ts", ".vue", ".uvue"):
                continue
            lines = _py_lines(root, p)
            for idx, line in enumerate(lines):
                if not TS_CATCH.search(line):
                    continue
                block = _ts_catch_body(lines, idx)
                if not block:
                    continue
                if any(
                    TS_LOG_CALL.search(ln) or re.search(r"\bthrow\b", ln)
                    for ln in block
                    if ln.strip()
                ):
                    continue
                non_empty = [ln.strip().rstrip(";") for ln in block if ln.strip()]
                if (
                    non_empty
                    and all(TS_SILENT_ONLY.match(ln) for ln in non_empty)
                    and not is_exempt(exemptions, "silent-catch", root, p)
                ):
                    out.append(
                        {
                            "rule": "silent-catch",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": f"line {idx + 1}: catch block swallows error with "
                            "no log/throw",
                        }
                    )
    return out


# --- magic status ----------------------------------------------------------


def _is_enum_member(node: ast.AST) -> bool:
    """True for `RuleEffect.ALLOWED`, `UserStatus.ACTIVE`, chains ending in an
    UPPER_SNAKE member (`X.Activity.ACTIVE`) or a trailing `.value`/`.name`."""
    if isinstance(node, ast.Attribute):
        if node.attr == "value" or node.attr == "name":
            return True
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", node.attr):
            return True
    return False


def _compare_status_words(compare: ast.Compare) -> list[tuple[str, int]]:
    """Return (status-word, lineno) pairs for `==`/`!=` against a word whose
    other side is not an enum member form."""
    if not all(isinstance(op, (ast.Eq, ast.NotEq)) for op in compare.ops):
        return []
    hits: list[tuple[str, int]] = []
    for lhs in [compare.left, *compare.comparators]:
        if not isinstance(lhs, ast.Constant) or not isinstance(lhs.value, str):
            continue
        if lhs.value not in STATUS_WORDS:
            continue
        for other in [compare.left, *compare.comparators]:
            if other is lhs:
                continue
            if isinstance(other, ast.Constant) and isinstance(other.value, str):
                # string-to-string comparison of two status words: still magic
                return [(lhs.value, compare.lineno)]
            if not _is_enum_member(other):
                hits.append((lhs.value, compare.lineno))
    return hits


def check_magic_status(exemptions: list[dict], py_roots: list[Path]) -> list[dict]:
    """Report bare-string status comparisons; enum-member comparisons pass."""
    out: list[dict] = []
    root = REPO_ROOT
    for r in py_roots:
        for p in iter_py(r):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Compare):
                    continue
                for word, lineno in _compare_status_words(node):
                    if is_exempt(exemptions, "magic-status", root, p):
                        continue
                    out.append(
                        {
                            "rule": "magic-status",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": f"line {lineno}: bare status string {word!r} — use "
                            "StrEnum member",
                        }
                    )
    return out
