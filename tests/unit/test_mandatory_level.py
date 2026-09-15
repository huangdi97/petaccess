"""BLK-LAYER-02 / ADR-023 — normative force (``mandatory_level``) regression suite.

The gap: ``AccessRule`` had no ``mandatory_level`` column, so every DB-sourced
LEGAL rule landed in the resolver's ``legal_other`` bucket and was excluded from
the governing set whenever any non-legal rule applied. A venue operator's
``allowed`` rule could therefore outvote 《上海市养犬管理条例》第二十三条.

These tests pin the fix end to end at the *unit* level (no database):

  A. vocabulary — one canonical spelling, one tolerated legacy alias
  B. resolver semantics — the mandatory legal floor (prohibition + conditions)
  C. publish boundary — a LEGAL candidate must declare its force; a bogus value
     is refused; the level is carried through publish()
  D. schema/introspection — the columns and enum values really exist
  E. property — a lower layer can never relax a mandatory legal prohibition
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.errors import ApiError
from app.models import AccessRule, RuleCandidate
from app.models.enums import MandatoryLevel, normalize_mandatory_level
from app.rulespec.v05_resolver import LayeredRule, RuleLayer, resolve
from app.services.publish_gate import MANDATORY_LEVEL_VALUES, validate_for_publish

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)


# --------------------------------------------------------------------------- A


def test_canonical_vocabulary_is_mandatory_advisory_operator_discretion():
    assert {e.value for e in MandatoryLevel} == {
        "mandatory",
        "advisory",
        "operator_discretion",
    }


def test_legacy_discretionary_normalises_to_operator_discretion():
    assert normalize_mandatory_level("discretionary") == "operator_discretion"


def test_normalise_preserves_unknown_and_none():
    # unknown is never coerced to a value; None stays None (never "mandatory")
    assert normalize_mandatory_level("bogus") == "bogus"
    assert normalize_mandatory_level(None) is None
    assert normalize_mandatory_level("mandatory") == "mandatory"


def test_publish_gate_accepts_legacy_spelling_but_not_unknown():
    assert "discretionary" in MANDATORY_LEVEL_VALUES
    assert "operator_discretion" in MANDATORY_LEVEL_VALUES
    assert "bogus" not in MANDATORY_LEVEL_VALUES


# --------------------------------------------------------------------------- D


def test_access_rule_has_mandatory_level_column():
    assert "mandatory_level" in AccessRule.__table__.columns


def test_rule_candidate_has_mandatory_level_column():
    assert "mandatory_level" in RuleCandidate.__table__.columns


def test_access_rule_mandatory_level_check_constraint_present():
    names = {c.name for c in AccessRule.__table__.constraints}
    assert "ck_access_rule_mandatory_level" in names


# --------------------------------------------------------------------------- B


def _legal(effect, *, mandatory="mandatory", conditions=(), id_="L1"):
    return LayeredRule(
        id=id_,
        animal_scope="dog",
        action="enter",
        effect=effect,
        rule_layer=RuleLayer.LEGAL.value,
        origin="legal",
        conditions=tuple(conditions),
        mandatory_level=mandatory,
    )


def _op(effect, *, id_="O1"):
    return LayeredRule(
        id=id_,
        animal_scope="dog",
        action="enter",
        effect=effect,
        rule_layer=RuleLayer.OPERATOR_POLICY.value,
        origin="operator_direct",
        mandatory_level=None,
    )


def _resolve(**over):
    kw = dict(
        legal=[],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    kw.update(over)
    return resolve(**kw)


def test_legal_rule_without_mandatory_level_is_not_the_floor():
    """BLK-LAYER-02 root cause: NULL/absent level ⇒ not mandatory ⇒ operator wins."""
    rs = _resolve(
        legal=[_legal("prohibited", mandatory=None)],
        operator_rules=[_op("allowed")],
    )
    assert rs.effect == "allowed"


def test_legal_rule_with_mandatory_level_is_the_floor():
    rs = _resolve(
        legal=[_legal("prohibited", mandatory="mandatory")],
        operator_rules=[_op("allowed")],
    )
    assert rs.effect == "prohibited"
    assert any(s[0].id == "O1" for s in rs.suppressed_rules)


def test_legacy_discretionary_legal_prohibition_is_not_the_floor():
    """The old spelling must not silently become binding either."""
    rs = _resolve(
        legal=[_legal("prohibited", mandatory="discretionary")],
        operator_rules=[_op("allowed")],
    )
    assert rs.effect == "allowed"


def test_mandatory_legal_condition_cannot_be_dropped_by_operator_allowed():
    """A mandatory legal obligation is a floor: 'allowed' cannot erase it."""
    rs = _resolve(
        legal=[
            _legal(
                "conditional",
                mandatory="mandatory",
                conditions=({"condition_type": "leash_required"},),
            )
        ],
        operator_rules=[_op("allowed")],
    )
    assert rs.effect == "conditional"
    assert "leash_required" in rs.obligations
    assert any(s[0].id == "O1" for s in rs.suppressed_rules)


def test_operator_may_still_be_more_restrictive_than_mandatory_legal():
    rs = _resolve(
        legal=[
            _legal(
                "conditional",
                mandatory="mandatory",
                conditions=({"condition_type": "leash_required"},),
            )
        ],
        operator_rules=[_op("prohibited")],
    )
    assert rs.effect == "prohibited"
    assert "leash_required" in rs.obligations


def test_mandatory_floor_survives_template_and_event_layers():
    rs = _resolve(
        legal=[_legal("prohibited", mandatory="mandatory")],
        template_rules=[
            LayeredRule(
                id="T1",
                animal_scope="dog",
                action="enter",
                effect="allowed",
                rule_layer="OPERATOR_POLICY",
                origin="template",
                mandatory_level=None,
            )
        ],
        event_rules=[
            LayeredRule(
                id="E1",
                animal_scope="dog",
                action="enter",
                effect="allowed",
                rule_layer="TEMPORARY_POLICY",
                origin="event",
                mandatory_level=None,
            )
        ],
    )
    assert rs.effect == "prohibited"
    suppressed = {s[0].id for s in rs.suppressed_rules}
    assert {"T1", "E1"} <= suppressed


# --------------------------------------------------------------------------- C


class _Stub:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Scalars:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return list(self._rows)


class _FakeSession:
    """Minimal Session stand-in for validate_for_publish (no database)."""

    def __init__(self, *, models, conflict_rows=()):
        #: models maps a real model class → {pk: row}
        self._by_model = models
        self._conflict_rows = list(conflict_rows)

    def get(self, model, pk):
        return self._by_model.get(model, {}).get(pk)

    def scalars(self, _stmt):
        return _Scalars(self._conflict_rows)


def _fake_session(**over):
    from app.models import Source
    from app.models.evidence import EvidenceBundle, SourceArtifact

    artifact = _Stub(
        id="art-1",
        content_hash="deadbeef",
        storage_allowed=True,
        display_allowed=True,
        redistribution_allowed=True,
        evidence_strength="primary_direct",
        collected_at=NOW,
    )
    bundle = _Stub(
        id="bundle-1",
        artifact_id="art-1",
        quoted_fragment="禁止携带犬只进入商场",
        content_hash="deadbeef",
        place_match_evidence={"matched_by": "name"},
    )
    source = _Stub(id="src-1", source_type="statute_or_regulation")
    models = {
        EvidenceBundle: {"bundle-1": bundle},
        SourceArtifact: {"art-1": artifact},
        Source: {"src-1": source},
    }
    return _FakeSession(models=models, **over)


def _candidate(**over):
    base = dict(
        id="cand-1",
        source_id="src-1",
        place_id="place-1",
        zone_id=None,
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer=RuleLayer.LEGAL.value,
        mandatory_level="mandatory",
        proposed_conditions=[],
        evidence_bundle_id="bundle-1",
        media_id=None,
        # ADR-025 scope columns. RuleCandidate really carries them (check 4c reads
        # them before any publish), so the double must too — otherwise this stub
        # describes an older schema than the one the guard actually sees.
        # None here means "no precise scope claimed", which is the honest default
        # for these cases: nothing is asserted about legal equivalence.
        source_scope_exact=None,
        subject_scope_normalized=None,
        normalization_type=None,
        normative_effect=None,
        holder_scope=None,
    )
    base.update(over)
    return _Stub(**base)


def test_publish_gate_refuses_legal_candidate_without_mandatory_level():
    db = _fake_session()
    cand = _candidate(mandatory_level=None)
    with pytest.raises(ApiError) as exc:
        validate_for_publish(db, cand, now=NOW)
    assert exc.value.code == "legal_requires_mandatory_level"


def test_publish_gate_allows_legal_candidate_with_mandatory_level():
    db = _fake_session()
    validate_for_publish(db, _candidate(mandatory_level="mandatory"), now=NOW)


def test_publish_gate_allows_non_legal_candidate_without_level():
    db = _fake_session()
    cand = _candidate(rule_layer=RuleLayer.OPERATOR_POLICY.value, mandatory_level=None)
    validate_for_publish(db, cand, now=NOW)


def test_publish_gate_rejects_unknown_mandatory_level_value():
    db = _fake_session()
    cand = _candidate(mandatory_level="totally-made-up")
    with pytest.raises(ApiError) as exc:
        validate_for_publish(db, cand, now=NOW)
    assert exc.value.code == "schema_unsupported"


def test_publish_gate_accepts_legacy_discretionary_value():
    db = _fake_session()
    cand = _candidate(rule_layer=RuleLayer.OPERATOR_POLICY.value, mandatory_level="discretionary")
    validate_for_publish(db, cand, now=NOW)


# --------------------------------------------------------------------------- E

_LEVELS = [None, "mandatory", "advisory", "operator_discretion", "discretionary"]


@settings(max_examples=200, deadline=None)
@given(
    legal_level=st.sampled_from(_LEVELS),
    op_effect=st.sampled_from(["allowed", "conditional"]),
)
def test_lower_layer_never_relaxes_a_mandatory_legal_prohibition(legal_level, op_effect):
    """Invariant: if a mandatory legal prohibition is in scope, no lower-layer
    allowed/conditional rule can make the resolved effect anything but
    'prohibited'."""
    legal = [
        LayeredRule(
            id="L1",
            animal_scope="dog",
            action="enter",
            effect="prohibited",
            rule_layer="LEGAL",
            origin="legal",
            mandatory_level=legal_level,
        )
    ]
    operator = [
        LayeredRule(
            id="O1",
            animal_scope="dog",
            action="enter",
            effect=op_effect,
            rule_layer="OPERATOR_POLICY",
            origin="operator_direct",
            mandatory_level=None,
        )
    ]
    rs = resolve(
        legal=legal,
        guidance=[],
        template_rules=[],
        operator_rules=operator,
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    if normalize_mandatory_level(legal_level) == "mandatory":
        assert rs.effect == "prohibited"
    else:
        # without a mandatory level the legal rule is not the floor
        assert rs.effect in {"allowed", "conditional"}


# --------------------------------------------------------------------------- F
# migration backfill semantics — verified on SQLite (no PostGIS needed)


def _sqlite_with_access_rule():
    import sqlalchemy as sa

    engine = sa.create_engine("sqlite://")
    md = sa.MetaData()
    sa.Table(
        "access_rule",
        md,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("rule_layer", sa.String(30), nullable=True),
        sa.Column("mandatory_level", sa.String(20), nullable=True),
    )
    md.create_all(engine)
    return engine


def _migration_sql():
    import importlib.util
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "services"
        / "api"
        / "migrations"
        / "versions"
        / "e3b7a1c4f920_access_rule_mandatory_level.py"
    )
    spec = importlib.util.spec_from_file_location("_mig_mandatory", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_migration_backfill_is_deterministic_and_idempotent():
    import sqlalchemy as sa

    mig = _migration_sql()
    engine = _sqlite_with_access_rule()
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO access_rule (id, rule_layer, mandatory_level) VALUES "
                "('a','LEGAL',NULL),"
                "('b','OPERATOR_POLICY',NULL),"
                "('c','TEMPORARY_POLICY',NULL),"
                "('d',NULL,NULL),"
                "('e','LEGAL','discretionary')"
            )
        )
        conn.execute(sa.text(mig._NORMALIZE.text.format(table="access_rule")))
        conn.execute(sa.text(mig._BACKFILL.text.format(table="access_rule")))
        first = dict(conn.execute(sa.text("SELECT id, mandatory_level FROM access_rule")).all())
        # run again: must be a no-op
        conn.execute(sa.text(mig._NORMALIZE.text.format(table="access_rule")))
        conn.execute(sa.text(mig._BACKFILL.text.format(table="access_rule")))
        second = dict(conn.execute(sa.text("SELECT id, mandatory_level FROM access_rule")).all())

    assert first == {
        "a": "mandatory",  # LEGAL → binding
        "b": "operator_discretion",  # operator layer → discretion
        "c": "operator_discretion",  # temporary layer → discretion
        "d": None,  # legacy NULL layer stays NULL (resolver flags REVIEW_REQUIRED)
        "e": "operator_discretion",  # legacy spelling normalised, never promoted
    }
    assert first == second  # idempotent


def test_migration_backfill_does_not_overwrite_existing_values():
    import sqlalchemy as sa

    mig = _migration_sql()
    engine = _sqlite_with_access_rule()
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO access_rule (id, rule_layer, mandatory_level) VALUES "
                "('x','LEGAL','advisory')"
            )
        )
        conn.execute(sa.text(mig._BACKFILL.text.format(table="access_rule")))
        row = conn.execute(
            sa.text("SELECT mandatory_level FROM access_rule WHERE id='x'")
        ).scalar_one()
    assert row == "advisory"  # an explicit reviewer choice is never clobbered


@settings(max_examples=100, deadline=None)
@given(level=st.sampled_from(_LEVELS), days=st.integers(min_value=0, max_value=3650))
def test_mandatory_floor_is_time_independent_within_window(level, days):
    """The floor does not depend on how old the rule is (freshness is a separate
    concern from normative force)."""
    start = NOW - timedelta(days=days)
    legal = [
        LayeredRule(
            id="L1",
            animal_scope="dog",
            action="enter",
            effect="prohibited",
            rule_layer="LEGAL",
            origin="legal",
            mandatory_level=level,
            effective_from=start,
        )
    ]
    rs = resolve(
        legal=legal,
        guidance=[],
        template_rules=[],
        operator_rules=[
            LayeredRule(
                id="O1",
                animal_scope="dog",
                action="enter",
                effect="allowed",
                rule_layer="OPERATOR_POLICY",
                origin="operator_direct",
            )
        ],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=NOW,
    )
    expected = "prohibited" if normalize_mandatory_level(level) == "mandatory" else "allowed"
    assert rs.effect == expected
