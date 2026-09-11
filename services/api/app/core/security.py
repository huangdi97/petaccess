"""Auth: password hashing, JWT issue/verify, current-user dependencies, RBAC."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import bcrypt
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFound, PermissionDenied, Unauthorized
from app.db.session import get_db
from app.models import User
from app.models.enums import UserRole

_bearer = HTTPBearer(auto_error=False)

# keyed by raw string values: String columns return plain str, not enums
ROLE_RANK: dict[str, int] = {
    "user": 0,
    "operator": 1,
    "trusted_verifier": 2,
    "moderator": 3,
    "admin": 4,
}


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, role: str) -> tuple[str, datetime]:
    settings = get_settings()
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "jti": uuid4().hex,
        "iat": datetime.now(UTC),
        "exp": expires,
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as e:
        raise Unauthorized("登录已过期") from e
    except jwt.InvalidTokenError as e:
        raise Unauthorized("无效凭证") from e
    if payload.get("type") != "access":
        raise Unauthorized("无效凭证类型")
    return payload


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise Unauthorized("缺少认证凭证")
    payload = decode_token(credentials.credentials)
    user = db.get(User, payload["sub"])
    if user is None or user.status != "active":
        raise Unauthorized("用户不可用")
    request.state.actor_user_id = user.id
    request.state.actor_role = str(user.role)
    return user


def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        return get_current_user(request, credentials, db)
    except (Unauthorized, NotFound):
        return None


def require_role(minimum: UserRole):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if ROLE_RANK[str(user.role)] < ROLE_RANK[minimum.value]:
            raise PermissionDenied(f"需要 {minimum.value} 或更高权限")
        return user

    return dependency
