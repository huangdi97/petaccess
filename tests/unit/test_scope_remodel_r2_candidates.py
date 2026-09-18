"""Regression locks for the SCOPE-REMODEL-R2 candidate materialiser (gate B2).

The failure this script exists to prevent is quiet: cloning a frozen row would
carry its scope fields along, producing a "new revision" that is byte-identical
to the old one and still fails the gate. These locks pin the parts that make a
cloned row a *different, publishable* row.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
_spec = importlib.util.spec_from_file_location(
    "scope_remodel_r2_candidates", SCRIPTS / "scope_remodel_r2_candidates.py"
)
assert _spec and _spec.loader
geo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(geo)


def test_dedup_key_is_deterministic_and_subject_scoped():
    """Same base+subject ⇒ same key; a different subject is a different row."""
    a = geo.dedup_key("3a04d4d1-aaac-4c3d-8364-9d1acf18ef35", "dog")
    b = geo.dedup_key("3a04d4d1-aaac-4c3d-8364-9d1acf18ef35", "dog")
    c = geo.dedup_key("3a04d4d1-aaac-4c3d-8364-9d1acf18ef35", "cat")
    assert a == b
    assert a != c


def test_cloned_columns_never_carry_the_old_scope():
    """The whole point of the revision is a new scope; cloning it would be a no-op."""
    for forbidden in (
        "animal_scope",
        "subject_scope_normalized",
        "normalization_type",
    ):
        assert forbidden not in geo.CLONED_COLUMNS
    # The source term must survive verbatim — it is the evidence, not a reading.
    assert "source_scope_exact" in geo.CLONED_COLUMNS


def test_revision_identity_is_stable():
    """Rows created by this script are attributable to one named revision."""
    assert geo.REVISION == "SCOPE-REMODEL-R2"
    assert geo.RUN_ID.startswith("SCOPE-R2-")


def test_empty_register_leaves_every_decision_blank(monkeypatch, tmp_path):
    """A template must never arrive pre-signed; the human fills the cells."""
    created = [
        {
            "candidate_id": "f2d0afde-006d-4914-8085-85edf0b78572",
            "place": "上海迪士尼乐园",
            "subject_scope_normalized": "dog",
            "supersedes_candidate_id": "3a04d4d1-aaac-4c3d-8364-9d1acf18ef35",
        }
    ]
    row = (
        "dog",  # animal_scope
        "dog",  # subject_scope_normalized
        "compound_term_split",  # normalization_type
        "prohibited",  # effect
        "OPERATOR_POLICY",  # rule_layer
        "operator_discretion",  # mandatory_level
        "动物（导盲犬除外）",  # source_scope_exact
        "prohibition",  # normative_effect
        "c757641b-407b-43cd-96b0-2469eafbfbac",  # evidence_bundle_id
        "2c868f71-96d3-40d9-894b-aec9315d7948",  # zone_id
        "上海迪士尼乐园",  # place name
        "全园",  # zone name
        "official_operator_policy",  # source_type
    )

    class _Cur:
        def execute(self, q, params=None):
            return None

        def fetchone(self):
            return row

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class _Conn:
        def cursor(self):
            return _Cur()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    import psycopg

    monkeypatch.setattr(psycopg, "connect", lambda url: _Conn())
    reg = geo.build_register("petaccess_publish_rehearsal_sr2", created)

    assert len(reg["rows"]) == 1
    assert reg["reviewer"] is None
    for cell in ("final_decision", "reviewer", "decided_at", "decision_note"):
        assert reg["rows"][0][cell] is None
    # The frozen row it replaces is recorded, so the supersession is auditable.
    assert reg["rows"][0]["supersedes_candidate_id"] == "3a04d4d1-aaac-4c3d-8364-9d1acf18ef35"
