"""The publisher must read the NEWEST sign-off register, never a superseded one.

Why this exists (found during GOV-01 packet cleanup):

``publish_reviewed_r1.py`` resolved its register with a hand-written two-branch
check — "use R2 if it exists, otherwise R1". When the R2-FINAL register was
generated for ADR-028, that check had no idea it existed, so the publisher kept
consuming **R2**. A reviewer filling in ``HUMAN_REVIEW_DECISIONS_R2_FINAL.json``
would therefore have signed a document the publish step never read: the choice
they made would be silently ignored, and publishing would act on the older table.

The register list is now declared once and resolved by order, so adding a
revision cannot repeat this class of drift. These tests pin that resolution.
"""

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "publish_reviewed_r1.py"
AUDIT = REPO / "docs" / "reality_audit"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("publish_reviewed_r1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_register_order_is_declared_newest_first(mod):
    """One declaration drives resolution; newest must come first."""
    order = mod._REGISTER_ORDER
    assert order.index("review_decisions_r2_final.json") == 0
    assert order.index("review_decisions_r2.json") < order.index("review_decisions_r1.json")


def test_active_register_is_newest_existing(mod):
    """Whatever exists in the audit dir, the publisher picks the newest."""
    present = [name for name in mod._REGISTER_ORDER if (AUDIT / name).exists()]
    assert present, "没有任何评审登记表存在，登记表生成流程可能已损坏"
    assert mod.DECISIONS.name == present[0]


def test_r2_final_register_supersedes_r2(mod):
    """Regression: the R2-FINAL table must win once it has been generated."""
    if not (AUDIT / "review_decisions_r2_final.json").exists():
        pytest.skip("尚未生成 R2-FINAL 登记表")
    assert mod.DECISIONS.name == "review_decisions_r2_final.json"


def _resolve(dirpath: Path, mod) -> str:
    """Apply the same resolution the module does, against an arbitrary dir."""
    return next(n for n in mod._REGISTER_ORDER if (dirpath / n).exists())


def test_resolution_falls_back_in_order(mod, tmp_path):
    """With only older registers present, the newest of *those* is picked."""
    (tmp_path / "review_decisions_r1.json").write_text("{}", encoding="utf-8")
    (tmp_path / "review_decisions_r2.json").write_text("{}", encoding="utf-8")
    assert _resolve(tmp_path, mod) == "review_decisions_r2.json"

    only_r1 = tmp_path / "nested"
    only_r1.mkdir()
    (only_r1 / "review_decisions_r1.json").write_text("{}", encoding="utf-8")
    assert _resolve(only_r1, mod) == "review_decisions_r1.json"


def test_registry_display_is_repo_relative(mod):
    """Operator-facing messages point at the active register, not a stale name."""
    shown = mod._registry_display()
    assert shown.endswith(".json")
    assert "review_decisions" in shown
    assert not shown.startswith("E:") and not shown.startswith("/")


def test_registry_display_survives_path_outside_repo(mod, monkeypatch, tmp_path):
    """``--registry`` may point outside the repo; reporting must not crash."""
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(mod, "DECISIONS", outside, raising=True)
    assert mod._registry_display() == str(outside)
