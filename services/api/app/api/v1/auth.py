"""Auth/session endpoints (design #31 /auth)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, Unauthorized
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db.session import get_db
from app.models import User
from app.models.enums import UserRole
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    exists = db.scalar(select(User).where(User.email == body.email))
    if exists:
        raise Conflict("该邮箱已注册")
    user = User(
        display_name=body.display_name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    token, expires_at = create_access_token(user.id, str(user.role))
    return TokenOut(access_token=token, expires_at=expires_at)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise Unauthorized("邮箱或密码不正确")
    if user.status != "active":
        raise Unauthorized("账号不可用")
    token, expires_at = create_access_token(user.id, str(user.role))
    return TokenOut(access_token=token, expires_at=expires_at)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
