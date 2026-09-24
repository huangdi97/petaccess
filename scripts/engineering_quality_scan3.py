#!/usr/bin/env python3
"""Engineering quality gate (v0.2.0 M1) — dead-code and duplicate-config scanner.

Two of the four Master Goal §40 gates missing from the M1 gate set:

* ``dead code``: a top-level function/class in a first-party module whose name
  never appears anywhere else in the first-party corpus (production + scripts)
  is either dead or only reachable through dynamic dispatch (Celery string task
  names, FastAPI aggregate routers, decorator injection). Genuinely dead
  symbols must be deleted; dynamic-dispatch symbols must be registered per
  symbol in `scripts/gate_exemptions.json` (rule=dead-code, symbol=<name>)
  with a TD reference — no whole-path exemptions.
* ``duplicate config``: the same KEY defined twice in one .env* file, a
  duplicate top-level key in a JSON config, or a repeated table header / key
  in pyproject.toml makes the effective value depend on parse order.

TS dead code is intentionally out of scope here: PR CI runs eslint and
vue-tsc (noUnusedLocals / no-unused-vars), which is the TS machine gate.

Pure stdlib; Python 3.11+.
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path

from engineering_quality_checks import REPO_ROOT, is_exempt, iter_py

ENV_KEY_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", re.MULTILINE)
TOML_TABLE_RE = re.compile(r"^\[([^\]]+)\]\s*$")
TOML_ARRAY_RE = re.compile(r"^\[\[([^\]]+)\]\]\s*$")
TOML_KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*=")


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


# --- dead code -------------------------------------------------------------


def _symbol_in_text(text: str, symbol: str) -> bool:
    return re.search(rf"\b{re.escape(symbol)}\b", text) is not None


def _dead_code_violations(corpus: dict[Path, str], py_roots: list[Path]) -> list[dict]:
    """A top-level symbol is dead when it never appears in the corpus except on
    its own definition line(s). Decorators/string task names count as usage
    only if they name the symbol; register dynamic-dispatch symbols explicitly.
    """
    out: list[dict] = []
    for path, text in corpus.items():
        if not any(_contains(p, path) for p in py_roots):
            continue  # scripts are corpus text for reference counting only
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        lines = text.splitlines()
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            name = node.name
            # Exclude only this symbol's definition lines in this file.
            def_linenos = {
                n.lineno
                for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and n.name == name
            }
            rest = "\n".join(line for i, line in enumerate(lines, 1) if i not in def_linenos)
            referenced = _symbol_in_text(rest, name)
            if not referenced:
                for other_path, other in corpus.items():
                    if other_path == path:
                        continue
                    if _symbol_in_text(other, name):
                        referenced = True
                        break
            if referenced:
                continue
            out.append(
                {
                    "rule": "dead-code",
                    "path": _rel(next(p for p in py_roots if _contains(p, path)), path),
                    "severity": "FAIL",
                    "detail": f"symbol {name!r} never referenced outside its definition",
                    "symbol": name,
                }
            )
    return out


def _contains(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def check_dead_code(exemptions: list[dict], py_roots: list[Path]) -> list[dict]:
    """Corpus = all first-party production files under py_roots + scripts/*.py."""
    corpus: dict[Path, str] = {}
    for root in py_roots:
        for p in iter_py(root):
            corpus[p] = p.read_text(encoding="utf-8", errors="replace")
    scripts = REPO_ROOT / "scripts"
    if scripts.is_dir():
        for p in sorted(scripts.rglob("*.py")):
            if p.name == "check_engineering_quality.py":
                continue  # the gate itself lists every rule name as text
            corpus[p] = p.read_text(encoding="utf-8", errors="replace")
    # First-party tests are first-party source: a symbol referenced only by
    # tests is not dead (plan FAIL condition: “定义行之外绝不出现于任何首方
    # 源码/脚本”). Include tests as corpus text (never as check subjects).
    for test_root in (REPO_ROOT / "tests", REPO_ROOT / "services/api/tests"):
        if test_root.is_dir():
            for p in sorted(test_root.rglob("*.py")):
                corpus[p] = p.read_text(encoding="utf-8", errors="replace")
    return [
        v
        for v in _dead_code_violations(corpus, py_roots)
        if not any(
            ex.get("rule") == "dead-code"
            and ex.get("symbol") == v["symbol"]
            and ex.get("path") == v["path"]
            for ex in exemptions
        )
    ]


# --- duplicate config ------------------------------------------------------


def _config_files(root: Path) -> list[Path]:
    env_bases = [root, root / "services/api"]
    if (root / "apps").is_dir():
        env_bases.extend(sorted((root / "apps").glob("*")))
    env = [p for b in env_bases if b.is_dir() for p in b.glob(".env*") if p.is_file()]
    json_cfg = [root / "package.json"]
    if (root / "apps").is_dir():
        json_cfg.extend(sorted((root / "apps").glob("*/package.json")))
    tauri = root / "apps/client-h5/src-tauri/tauri.conf.json"
    if tauri.is_file():
        json_cfg.append(tauri)
    tom = [
        p
        for w in (root, root / "services/api", root / "services/worker")
        if (p := w / "pyproject.toml").is_file()
    ]
    return [*env, *json_cfg, *tom]


def _top_level_json_keys(text: str) -> Counter[str]:
    """Count keys at brace depth 1: direct members of the root JSON object.

    A small state machine (not a regex) so escaped quotes and braces inside
    string values cannot miscount depth or crash on a dangling quote.
    """
    depth, keys = 0, Counter()
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            # scan to the end of this string literal, honoring backslash escapes
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    break
                j += 1
            if j >= n:
                break  # unterminated string: stop, file is malformed anyway
            closing = j
            # a key is `"..."` immediately followed (after whitespace) by `:`
            k = closing + 1
            while k < n and text[k] in " \t":
                k += 1
            if depth == 1 and k < n and text[k] == ":":
                keys[text[i + 1 : closing]] += 1
            i = closing + 1
            continue
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        i += 1
    return keys


def _env_duplicates(text: str) -> list[str]:
    """Duplicate KEY= keys within one .env file body."""
    counter: Counter[str] = Counter()
    for m in ENV_KEY_RE.finditer(text):
        counter[m.group(1)] += 1
    return [k for k, c in counter.items() if c > 1]


def _toml_duplicates(text: str) -> list[str]:
    """Repeated [table] headers and repeated keys inside one table."""
    out: list[str] = []
    tables_seen: set[str] = set()
    table_keys: Counter[str] = Counter()
    table: str | None = None
    for line in text.splitlines():
        am = TOML_ARRAY_RE.match(line)
        if am:
            table, table_keys = am.group(1).strip(), Counter()
            continue
        tm = TOML_TABLE_RE.match(line)
        if tm:
            table = tm.group(1).strip()
            if table in tables_seen:
                out.append(f"table [{table}] repeated")
            tables_seen.add(table)
            table_keys = Counter()
            continue
        km = TOML_KEY_RE.match(line)
        if km and table is not None:
            table_keys[km.group(1)] += 1
    out.extend(
        f"[{table}] key {key!r} repeated {count}x" for key, count in table_keys.items() if count > 1
    )
    return out


def check_duplicate_config(exemptions: list[dict]) -> list[dict]:
    out: list[dict] = []
    root = REPO_ROOT

    def not_exempt(p: Path) -> bool:
        return not is_exempt(exemptions, "duplicate-config", root, p)

    for p in _config_files(root):
        text = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix == ".env" or p.name.startswith(".env"):
            for key in _env_duplicates(text):
                if not_exempt(p):
                    out.append(
                        {
                            "rule": "duplicate-config",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": f"KEY {key!r} defined more than once in one .env file",
                        }
                    )
        elif p.name in ("package.json", "tauri.conf.json"):
            for key, count in _top_level_json_keys(text).items():
                if count > 1 and not_exempt(p):
                    out.append(
                        {
                            "rule": "duplicate-config",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": f"JSON top-level key {key!r} repeated {count}x",
                        }
                    )
        elif p.name == "pyproject.toml":
            for detail in _toml_duplicates(text):
                if not_exempt(p):
                    out.append(
                        {
                            "rule": "duplicate-config",
                            "path": _rel(root, p),
                            "severity": "FAIL",
                            "detail": detail,
                        }
                    )
    return out
