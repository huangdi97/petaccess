"""Unit tests for the M1 engineering quality gate (scripts/engineering_quality_*).

Covers the non-blind exemption mechanics and each scanner on small fixtures:
an exempted violation disappears, an unjustified one is reported, cycles are
detected, and tracked TODOs (TODO(PROJ-123):) pass while bare ones fail.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from engineering_quality_checks import (
    check_functions,
    check_size,
    dependency_cycles,
    iter_frontend,
    iter_py,
)
from engineering_quality_scan import check_todos, check_ts_colors, check_type_escapes
from engineering_quality_scan2 import check_magic_status, check_silent_catches
from engineering_quality_scan3 import (
    _env_duplicates,
    _top_level_json_keys,
    check_dead_code,
)


def test_no_exemptions_matches_policy() -> None:
    assert check_todos([], [], []) == []  # empty input, nothing to flag


def make_py_tree(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / "repo"
    for name, content in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def test_iter_py_skips_migrations(tmp_path: Path) -> None:
    root = make_py_tree(
        tmp_path,
        {
            "app/a.py": "x = 1\n",
            "migrations/versions/abc.py": "x = 2\n",
        },
    )
    names = [p.name for p in iter_py(root)]
    assert names == ["a.py"]


def test_iter_frontend_skips_generated(tmp_path: Path) -> None:
    root = make_py_tree(
        tmp_path,
        {
            "src/View.vue": "<template><div/></template>\n",
            "src/schema.d.ts": "declare const x: any;\n",
        },
    )
    names = [p.name for p in iter_frontend(root)]
    assert names == ["View.vue"]


def test_check_size_flags_over300(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"app/big.py": "\n" * 301})
    hits = check_size([], [root], [])
    assert any(v["rule"] == "file>300" for v in hits)


def test_check_size_exemption_hides_violation(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"app/big.py": "\n" * 301})
    ex = [{"rule": "file>300", "path": "**/big.py", "reason": "test", "reference": "TD-XXX"}]
    assert check_size(ex, [root], []) == []


def test_py_metrics_reports_big_function(tmp_path: Path) -> None:
    body = "\n".join(f"    p{i} = {i}" for i in range(70))
    root = make_py_tree(tmp_path, {"app/f.py": f"def long():\n{body}\n"})
    assert any(v["rule"] == "fn>60" for v in check_functions([], [root]))


def test_py_metrics_reports_complexity(tmp_path: Path) -> None:
    src = "def c():\n" + "".join(f"    if x{i}:\n        pass\n" for i in range(20))
    root = make_py_tree(tmp_path, {"app/c.py": src})
    assert any(v["rule"] == "cyclo>15" for v in check_functions([], [root]))


def test_dependency_cycles_detected(tmp_path: Path) -> None:
    root = make_py_tree(
        tmp_path,
        {
            "app/a.py": "import b\n",
            "app/b.py": "import a\n",
        },
    )
    assert len(dependency_cycles([root])) >= 1


def test_dependency_cycles_clean(tmp_path: Path) -> None:
    root = make_py_tree(
        tmp_path,
        {
            "app/a.py": "import c\n",
            "app/b.py": "import c\n",
            "app/c.py": "pass\n",
        },
    )
    assert dependency_cycles([root]) == []


def test_todo_tracked_passes(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"src/a.ts": "// TODO(PROJ-123): remove after migration\n"})
    assert check_todos([], [], [root]) == []


def test_todo_bare_fails(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"src/a.ts": "// TODO: fix this later\n"})
    hits = check_todos([], [], [root])
    assert any(v["rule"] == "todo" for v in hits)


def test_type_escape_reported_and_exempted(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"app/e.py": "x: Any = 1  # noqa\n"})
    assert any(v["rule"] == "type-escape" for v in check_type_escapes([], [root], []))
    ex = [{"rule": "type-escape", "path": "**/e.py", "reason": "test", "reference": "TD-XXX"}]
    assert check_type_escapes(ex, [root], []) == []


def test_hardcoded_color_detected(tmp_path: Path) -> None:
    root = make_py_tree(
        tmp_path,
        {"src/V.vue": "<style>.a{color:#ff0000}</style>\n", "src/tokens.css": ":root{--x:#fff}\n"},
    )
    hits = check_ts_colors([], [root])
    assert any(v["rule"] == "hardcoded-color" and "V.vue" in v["path"] for v in hits)
    assert not any("tokens.css" in v["path"] for v in hits)


# --- silent catch (v0.2.0 M1 §40) -----------------------------------------


def test_silent_catch_pass_reported(tmp_path: Path) -> None:
    root = make_py_tree(
        tmp_path,
        {"app/a.py": "def f():\n    try:\n        g()\n    except Exception:\n        pass\n"},
    )
    hits = check_silent_catches([], [root], [])
    assert any(v["rule"] == "silent-catch" for v in hits)


def test_silent_catch_constant_return_reported(tmp_path: Path) -> None:
    root = make_py_tree(
        tmp_path,
        {"app/a.py": "def f():\n    try:\n        g()\n    except Exception:\n        return []\n"},
    )
    assert any(v["rule"] == "silent-catch" for v in check_silent_catches([], [root], []))


def test_silent_catch_with_debug_log_ok(tmp_path: Path) -> None:
    root = make_py_tree(
        tmp_path,
        {
            "app/a.py": (
                "import logging\n"
                "def f():\n"
                "    try:\n"
                "        g()\n"
                "    except Exception as exc:\n"
                "        logging.getLogger('x').debug('boom %s', exc)\n"
                "        return []\n"
            )
        },
    )
    assert check_silent_catches([], [root], []) == []


# --- magic status (v0.2.0 M1 §40) -----------------------------------------


def test_magic_status_bare_string_reported(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"app/a.py": "if effect == 'allowed':\n    pass\n"})
    hits = check_magic_status([], [root])
    assert any(v["rule"] == "magic-status" and "allowed" in v["detail"] for v in hits)


def test_magic_status_enum_member_ok(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"app/a.py": "if effect == RuleEffect.ALLOWED:\n    pass\n"})
    assert check_magic_status([], [root]) == []


def test_magic_status_non_status_word_ok(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"app/a.py": "if pet == 'animal':\n    pass\n"})
    assert check_magic_status([], [root]) == []


# --- dead code (v0.2.0 M1 §40) ---------------------------------------------


def test_dead_code_unreferenced_reported(tmp_path: Path) -> None:
    sym = f"only_here_{uuid.uuid4().hex[:6]}"
    root = make_py_tree(tmp_path, {"app/a.py": f"def {sym}():\n    pass\n"})
    hits = check_dead_code([], [root])
    assert any(v["rule"] == "dead-code" and v["symbol"] == sym for v in hits)


def test_dead_code_imported_ok(tmp_path: Path) -> None:
    sym = f"shared_helper_{uuid.uuid4().hex[:6]}"
    root = make_py_tree(
        tmp_path,
        {
            "app/a.py": f"def {sym}():\n    pass\n",
            "app/b.py": f"from a import {sym}\n",
        },
    )
    assert check_dead_code([], [root]) == []


def test_dead_code_symbol_exemption_ok(tmp_path: Path) -> None:
    sym = f"only_here_{uuid.uuid4().hex[:6]}"
    root = make_py_tree(tmp_path, {"app/a.py": f"def {sym}():\n    pass\n"})
    ex = [
        {
            "rule": "dead-code",
            "path": "app/a.py",
            "symbol": sym,
            "reason": "dynamic dispatch test",
            "reference": "TD-028",
        }
    ]
    assert check_dead_code(ex, [root]) == []


# --- duplicate config (v0.2.0 M1 §40) --------------------------------------


def test_duplicate_config_env_dup_reported(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"x.env": "A=1\nA=2\nB=3\n"})
    p = root / "x.env"
    assert "A" in _env_duplicates(p.read_text(encoding="utf-8"))


def test_duplicate_config_env_clean(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"x.env": "A=1\nB=3\n"})
    assert _env_duplicates((root / "x.env").read_text(encoding="utf-8")) == []


def test_duplicate_config_json_dup_reported(tmp_path: Path) -> None:
    root = make_py_tree(tmp_path, {"pkg.json": '{\n  "name": "a",\n  "name": "b",\n  "v": 1\n}\n'})
    keys = _top_level_json_keys((root / "pkg.json").read_text(encoding="utf-8"))
    assert keys["name"] == 2
