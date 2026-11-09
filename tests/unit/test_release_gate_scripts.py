"""Fail-closed release gate scripts must keep failing on bad input.

`release-ci.yml` refuses to build a signed artifact unless the packaged runtime
points at a real HTTPS PetAccess API, and the runtime-config generator refuses
to emit one otherwise. Both guarantees live in small Node scripts that nothing
exercised: the signed jobs have been skipped on every run so far, so a relaxed
check would go unnoticed until the first real release.

These tests drive the scripts as subprocesses exactly as CI does, so the
contract is pinned without importing anything into the Python test process.
Node is optional here: the backend job is Python-only, so the module skips
rather than failing where the runner has no node.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "scripts" / "release" / "generate_tauri_release_config.cjs"
PREFLIGHT = REPO_ROOT / "scripts" / "release" / "verify_public_api.cjs"

needs_node = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is not installed in this job"
)


def _run(script: Path, args: list[str], api_base: str | None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("PETACCESS_PUBLIC_API_BASE", None)
    env.pop("PETACCESS_REQUIRE_REAL_MAP", None)
    if api_base is not None:
        env["PETACCESS_PUBLIC_API_BASE"] = api_base
    return subprocess.run(
        ["node", str(script), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=120,
    )


@needs_node
def test_generator_refuses_missing_api_base(tmp_path: Path) -> None:
    result = _run(GENERATOR, [str(tmp_path / "out.json")], None)
    assert result.returncode == 1
    assert "PETACCESS_PUBLIC_API_BASE is required" in result.stderr
    assert not (tmp_path / "out.json").exists(), "must not emit a config without an API base"


@needs_node
@pytest.mark.parametrize(
    ("api_base", "expected"),
    [
        ("http://petaccess.example.org/api/v1", "must use https"),
        ("https://petaccess.example.org/", "must end with /api/v1"),
        ("https://petaccess.example.org/api/v1?x=1", "must not contain query parameters"),
    ],
)
def test_generator_rejects_unusable_api_base(tmp_path: Path, api_base: str, expected: str) -> None:
    result = _run(GENERATOR, [str(tmp_path / "out.json")], api_base)
    assert result.returncode == 1
    assert expected in result.stderr
    assert not (tmp_path / "out.json").exists()


@needs_node
def test_generator_emits_strict_csp_without_dev_origins(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    result = _run(GENERATOR, [str(out)], "https://petaccess.example.org/api/v1")
    assert result.returncode == 0, result.stderr

    csp = json.loads(out.read_text(encoding="utf-8"))["app"]["security"]["csp"]
    # The signed build must reach the declared API and no development server.
    # Tauri's own http://ipc.localhost and http://asset.localhost are part of the
    # runtime contract, so "no localhost at all" would be the wrong assertion:
    # what must be absent is the dev-server / emulator-host origins.
    assert "https://petaccess.example.org" in csp
    assert "127.0.0.1" not in csp
    assert "10.0.2.2" not in csp
    assert ":5175" not in csp and ":5176" not in csp
    assert "http://ipc.localhost" in csp


@needs_node
def test_preflight_refuses_missing_api_base() -> None:
    result = _run(PREFLIGHT, [], None)
    assert result.returncode == 1
    assert "PETACCESS_PUBLIC_API_BASE is required" in result.stderr


@needs_node
@pytest.mark.parametrize(
    ("api_base", "expected"),
    [
        ("http://petaccess.example.org/api/v1", "must use https"),
        ("https://user:secret@petaccess.example.org/api/v1", "must not contain embedded"),
        ("https://petaccess.example.org/api/v1?x=1", "must not contain query parameters"),
        ("https://petaccess.example.org/", "must end with /api/v1"),
    ],
)
def test_preflight_rejects_unusable_api_base(api_base: str, expected: str) -> None:
    result = _run(PREFLIGHT, [], api_base)
    assert result.returncode == 1
    assert expected in result.stderr
