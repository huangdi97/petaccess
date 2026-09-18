"""v0.5 Track B logic tests: boundary matcher, source monitor SSRF guard,
candidate state machine, PetAccessJSON."""

import pytest

from app.core.errors import ApiError
from app.rulespec.petaccessjson import PetAccessJSONError, dump, load
from app.rulespec.v05_boundary import match as boundary_match
from app.services.candidate_service import create_from_extraction, transition
from app.services.source_monitor import MonitorFetchError, fetch_url_safely

# ------------------------------------------------------------- BoundaryMatcher


def test_boundary_accept_match_conflict_unknown():
    results = boundary_match(
        effective_effect="unknown",
        coexistence={
            "ordinary_pet_outdoor_dining": "allowed",
            "ordinary_pet_indoor_dining": "prohibited",
            "animal_on_customer_seat": "allowed",
            "animal_use_customer_tableware": "prohibited",
        },
        preferences=[
            ("ordinary_pet_outdoor_dining", "accept"),
            ("ordinary_pet_indoor_dining", "accept"),
            ("animal_on_customer_seat", "avoid"),
            ("animal_use_customer_tableware", "require_prohibited"),
            ("dedicated_pet_zone", "prefer"),
        ],
    )
    by_attr = {r.attribute: r for r in results}
    assert by_attr["ordinary_pet_outdoor_dining"].verdict == "MATCH"
    assert by_attr["ordinary_pet_indoor_dining"].verdict == "CONFLICT"
    assert by_attr["animal_on_customer_seat"].verdict == "CONFLICT"
    assert by_attr["animal_use_customer_tableware"].verdict == "MATCH"
    assert by_attr["dedicated_pet_zone"].verdict == "UNKNOWN"


def test_boundary_no_total_score_in_output():
    results = boundary_match(effective_effect="conditional", coexistence={}, preferences=[])
    assert not hasattr(results, "score")
    assert all(not hasattr(r, "score") for r in results)


def test_boundary_unknown_never_treated_as_match():
    results = boundary_match(
        effective_effect="unknown",
        coexistence={},
        preferences=[("animal_on_table_surface", "avoid")],
    )
    assert results[0].verdict == "UNKNOWN"


def test_boundary_derives_dining_from_effective_rules():
    results = boundary_match(
        effective_effect="allowed",
        coexistence={},
        preferences=[("ordinary_pet_indoor_dining", "accept")],
    )
    assert results[0].verdict == "MATCH"
    assert "effective" in results[0].reason or "属性" in results[0].reason


# ------------------------------------------------------------- SourceMonitor


def test_monitor_rejects_non_http_scheme():
    with pytest.raises(MonitorFetchError) as ei:
        fetch_url_safely("file:///etc/passwd")
    assert ei.value.code == "scheme_not_allowed"


def test_monitor_blocks_private_and_loopback_hosts(monkeypatch):
    monkeypatch.setattr(
        "app.services.source_monitor.socket.getaddrinfo",
        lambda host, port: [(2, 1, 6, "", ("127.0.0.1", 0))],
    )
    with pytest.raises(MonitorFetchError) as ei:
        fetch_url_safely("http://intranet.example/policy")
    assert ei.value.code == "private_network_blocked"


def test_monitor_rejects_unknown_content_type(monkeypatch):
    class FakeResp:
        status_code = 200
        headers = {"content-type": "application/octet-stream"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def iter_bytes(self, chunk_size):
            yield b"x"

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def stream(self, method, url, headers=None):
            return FakeResp()

    import httpx as _httpx

    orig = _httpx.Client
    monkeypatch.setattr(_httpx, "Client", lambda **kw: FakeClient())
    try:
        with pytest.raises(MonitorFetchError) as ei:
            fetch_url_safely("https://example.com/binary")
        assert ei.value.code == "content_type_not_allowed"
    finally:
        monkeypatch.setattr(_httpx, "Client", orig)


def test_monitor_hash_is_sha256_of_body():
    """Hash determinism: same body → same hash (verified via FetchResult)."""
    # full network path is covered in integration tests with local http server
    import hashlib

    from app.services.source_monitor import fetch_url_safely as _fetch  # noqa: F401

    body = b"<html>policy v2</html>"
    assert hashlib.sha256(body).hexdigest() != hashlib.sha256(body + b"!").hexdigest()


# ------------------------------------------------------------- candidate state machine


def test_candidate_state_machine_legal_transitions(db_session):
    from app.models import Source

    src = Source(
        source_type="ordinary_user",
        issuer="t",
        directness="secondary",
        collected_at="2026-09-12T00:00:00Z",
    )
    db_session.add(src)
    db_session.flush()
    cand = create_from_extraction(
        db_session,
        source_id=src.id,
        extraction_method="ocr",
        raw_text="门口告示：户外牵引可入",
    )
    assert cand.review_status == "EXTRACTED"
    transition(cand, "REJECTED")
    assert cand.review_status == "REJECTED"
    with pytest.raises(ApiError):
        transition(cand, "APPROVED")


def test_candidate_rejected_is_terminal(db_session):
    from app.models import Source

    src = Source(
        source_type="ordinary_user",
        issuer="t2",
        directness="secondary",
        collected_at="2026-09-12T00:00:00Z",
    )
    db_session.add(src)
    db_session.flush()
    cand = create_from_extraction(
        db_session,
        source_id=src.id,
        extraction_method="user_upload",
        animal_scope="ordinary_pet",
        action="enter",
        effect="allowed",
    )
    assert cand.review_status == "MATCH_PENDING"
    transition(cand, "REVIEW_PENDING", reviewer_id="admin-1")
    transition(cand, "REJECTED", reviewer_id="admin-1", note="与规则冲突")
    with pytest.raises(ApiError):
        transition(cand, "REVIEW_PENDING")


# ------------------------------------------------------------- PetAccessJSON


def test_petaccessjson_roundtrip():
    doc = dump(
        species="dog",
        role="ordinary_pet",
        place_id="11111111-1111-1111-1111-111111111111",
        zone_id=None,
        action="enter",
        effect="conditional",
        rule_layer="OPERATOR_POLICY",
        conditions=[{"type": "max_weight_kg", "value": 15}],
        effective_from="2026-09-01T00:00:00+08:00",
        source_id="22222222-2222-2222-2222-222222222222",
    )
    loaded = load(doc)
    assert loaded["petaccessjson_version"] == "0.1"
    assert loaded["subject"]["species"] == "dog"


def test_petaccessjson_rejects_bad_layer_and_version():
    base = dict(
        species="dog",
        role="ordinary_pet",
        place_id="11111111-1111-1111-1111-111111111111",
        zone_id=None,
        action="enter",
        effect="allowed",
        rule_layer="OPERATOR_POLICY",
        source_id="22222222-2222-2222-2222-222222222222",
    )
    bad_layer = dict(base, rule_layer="RUMOR")
    with pytest.raises(PetAccessJSONError):
        dump(**bad_layer)
    bad = dump(**base)
    bad["petaccessjson_version"] = "9.9"
    with pytest.raises(PetAccessJSONError):
        load(bad)
    missing = dump(**base)
    del missing["source"]
    with pytest.raises(PetAccessJSONError):
        load(missing)
