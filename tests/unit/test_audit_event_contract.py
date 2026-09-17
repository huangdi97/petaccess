"""§14 / §15 / §16 — the publish audit contract, in one place.

The publish contract drifted because the action names were string literals:
the HTTP exception route wrote ``candidate.publish_exception`` while nothing
else ever did, and the verifier was the only thing that noticed. These tests
lock the parts that make drift impossible or at least loud:

* the vocabulary is canonical and complete — no route may invent a name;
* the publish events are the ones the verifier expects, read from the same
  constant the publisher uses;
* an audit row names a real target. The ``target_id == "None"`` bug is exactly
  what a literal-only contract looks like in production: 2,647 rows naming
  nothing;
* a reconciliation is labelled as one. A backfilled row must never be
  indistinguishable from an observed event.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.core.audit_events import (
    AUDIT_BACKFILL_REASON,
    BACKFILL_FLAG,
    ORIGINAL_PUBLISH_AT,
    PUBLISH_AUDIT_REQUIRED,
    AuditEvent,
    canonical_events,
    is_canonical,
)

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services" / "api"


def test_vocabulary_has_no_duplicate_values() -> None:
    values = [e.value for e in AuditEvent]
    assert len(values) == len(set(values)), "审计动作名重复会让血缘统计失真"


def test_publish_events_are_the_canonical_three() -> None:
    assert {
        AuditEvent.CANDIDATE_TRANSITION.value,
        AuditEvent.CANDIDATE_PUBLISH.value,
        AuditEvent.CANDIDATE_PUBLISH_EXCEPTION.value,
    } == set(PUBLISH_AUDIT_REQUIRED)


def test_publish_audit_required_is_the_verifier_vocabulary() -> None:
    """Publisher and verifier must read the same list (§13).

    `verify_publish_r3.py` asserts on these exact strings. If they were written
    independently, the two could drift apart again without any test failing —
    which is how the missing ``candidate.publish_exception`` rows went unnoticed.
    """
    verifier = Path(ROOT / "scripts" / "verify_publish_r3.py").read_text(encoding="utf-8")
    for action in sorted(PUBLISH_AUDIT_REQUIRED):
        assert f"'{action}'" in verifier, f"校验器未使用 canonical 事件 {action}"


def test_no_literal_audit_actions_in_routes() -> None:
    """Every writer imports the constant; a literal is a future drift."""
    offenders: list[str] = []
    pattern = re.compile(r'action\s*=\s*["\']([a-z_]+\.[a-z_]+)["\']')
    for path in sorted(SERVICES.rglob("*.py")):
        if "audit_events.py" in str(path):
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in pattern.finditer(line):
                # `action` is also a field name on RuleCandidate/AccessRule; only
                # audit writes carry an action that looks like an event name.
                if match.group(1) in _VALUE_SET:
                    offenders.append(f"{path.relative_to(ROOT)}:{lineno} -> {match.group(1)}")
    assert not offenders, f"审计动作必须引用 AuditEvent 常量：{offenders}"


_VALUE_SET = set(canonical_events())


def test_creating_a_source_records_its_real_id() -> None:
    """The ``target_id == "None"`` regression (§23 MEDIUM, root cause).

    An un-flushed ORM object has no primary key, so ``str(obj.id)`` writes the
    *string* "None" and the audit row can never be traced back. The routes were
    fixed by flushing before auditing; this asserts the fix is structurally
    present rather than trusting a code review.
    """
    sources = (SERVICES / "app" / "api" / "v1" / "sources.py").read_text(encoding="utf-8")
    audit_call = sources.split("record_audit(")[1]
    assert "db.flush()" in sources.split("record_audit(")[0], (
        "source.create 的审计发生在 flush 之前会把 target_id 写成字符串 'None'"
    )
    assert "source.id" in audit_call


def test_audit_target_id_is_never_the_string_none() -> None:
    """A guard for the same defect wherever else it might reappear."""
    offenders: list[str] = []
    pattern = re.compile(r"target_id\s*=\s*str\(([A-Za-z_][\w]*)\.id\)")
    for path in sorted(SERVICES.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            prefix = text[: match.start()]
            last_flush = prefix.rfind("db.flush()")
            last_add = prefix.rfind("db.add(")
            if last_add > last_flush:
                offenders.append(f"{path.relative_to(ROOT)} -> {match.group(0)}")
    assert not offenders, f"db.add 之后、db.flush 之前取 id 会产生 'None'：{offenders}"


def test_record_audit_refuses_an_unusable_target_id() -> None:
    """The write-time tripwire for the same defect.

    The scan can only find rows that were already written. Refusing to write
    them is what stops the next 2,647 — and it fails in the request that
    caused it, where the object being audited is still in hand.
    """
    from app.core.audit import record_audit

    for bad in ("None", "", None):
        with pytest.raises(ValueError, match="no usable target_id"):
            record_audit(
                object(),  # a Session is never touched: the guard fires first
                actor_user_id=None,
                actor_role="system",
                action=AuditEvent.CANDIDATE_PUBLISH.value,
                target_type="place",
                target_id=bad,  # type: ignore[arg-type]
            )


@pytest.mark.parametrize("name", ["candidate.publish", "candidate.publish_exception"])
def test_canonical_names_are_recognised(name: str) -> None:
    assert is_canonical(name)
    assert not is_canonical("candidate.publishd")


def test_backfill_is_labelled_and_dated() -> None:
    """§16 — a reconciled row must say so, and must not fake its timestamp.

    The backfill script is the only sanctioned writer, so the contract is
    asserted against it directly: the row it builds carries
    ``backfilled=true``, the reconciliation reason, and the *original* publish
    instant in its own field.
    """
    script = (ROOT / "scripts" / "backfill_publish_exception_audit.py").read_text(encoding="utf-8")
    assert BACKFILL_FLAG in script and "True" in script
    assert AUDIT_BACKFILL_REASON in script
    assert ORIGINAL_PUBLISH_AT in script
    assert "now()" in script, "事件自身的 created_at 必须是回填时刻，而不是伪造的原始时刻"


def test_backfill_receipt_records_the_original_instant() -> None:
    """The executed reconciliation is on disk and labels every row."""
    receipt = ROOT / "artifacts" / "integrity_final_closure" / "AUDIT_BACKFILL_RECEIPT.json"
    if not receipt.is_file():
        pytest.skip("回填尚未执行；此测试在回填产物存在时校验其内容")
    doc = json.loads(receipt.read_text(encoding="utf-8"))
    assert doc["backfill_count"] == 3
    assert doc["inserted"] == 3
    for row in doc["rows"]:
        if not row["needs_backfill"]:
            continue
        assert row["published_at"], "回填必须记录原始发布时刻"
