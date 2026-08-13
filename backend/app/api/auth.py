from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import settings
from app.core.rbac import Role
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.common import TokenOut, UserOut
from app.schemas.requests import LoginRequest, RegisterRequest
from app.services.audit import audit
from app.services.rate_limit import rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.auth_cookie_name,
        token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


def validate_browser_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in settings.cors_origin_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid browser origin")


@router.post("/register", response_model=TokenOut, dependencies=[Depends(rate_limit("register"))])
def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> TokenOut:
    validate_browser_origin(request)
    if payload.role not in {role.value for role in Role}:
        raise HTTPException(status_code=400, detail="Invalid role")
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    # Public registration is intentionally least-privilege. Seed/admin workflows assign elevated roles.
    user = User(email=payload.email.lower(), hashed_password=hash_password(payload.password), role=Role.viewer.value)
    db.add(user)
    db.flush()
    audit(db, user.id, "auth.register", "user", str(user.id), {"role": user.role})
    db.commit()
    token = create_access_token(str(user.id), user.role)
    set_session_cookie(response, token)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut, dependencies=[Depends(rate_limit("login"))])
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> TokenOut:
    validate_browser_origin(request)
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    audit(db, user.id, "auth.login", "user", str(user.id))
    db.commit()
    token = create_access_token(str(user.id), user.role)
    set_session_cookie(response, token)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    validate_browser_origin(request)
    response.delete_cookie(settings.auth_cookie_name, path="/", secure=settings.auth_cookie_secure, samesite="lax")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.model_validate(user)
