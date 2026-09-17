"""Audit logging for high-impact operations (design #25, #27)."""

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditLog


def record_audit(
    db: Session,
    *,
    request: Request | None = None,
    actor_user_id: str | None,
    actor_role: str | None,
    action: str,
    target_type: str,
    target_id: str,
    before_state: dict | None = None,
    after_state: dict | None = None,
    detail: dict | None = None,
) -> None:
    # Fail loudly at write time. An un-flushed ORM instance has no primary key,
    # so ``str(obj.id)`` yields the literal "None" and the row names no object —
    # a defect that is invisible when written and only surfaces later as
    # ``AUDIT_TARGET_ID_UNUSABLE`` in the integrity scan, by which point the
    # identity it should have recorded is gone. Callers must ``db.flush()``.
    if not target_id or target_id == "None":
        raise ValueError(
            f"audit row for {action}/{target_type} has no usable target_id "
            f"({target_id!r}) — db.flush() before recording the audit"
        )
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            before_state=before_state,
            after_state=after_state,
            request_id=getattr(request.state, "request_id", None) if request else None,
            ip_address=(request.client.host if request and request.client else None),
            detail=detail,
        )
    )
