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
