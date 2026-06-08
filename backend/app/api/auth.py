from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.rbac import Role
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.common import TokenOut, UserOut
from app.schemas.requests import LoginRequest, RegisterRequest
from app.services.audit import audit
from app.services.rate_limit import rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, dependencies=[Depends(rate_limit("register"))])
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenOut:
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
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut, dependencies=[Depends(rate_limit("login"))])
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    audit(db, user.id, "auth.login", "user", str(user.id))
    db.commit()
    return TokenOut(access_token=create_access_token(str(user.id), user.role), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)) -> UserOut:
    return UserOut.model_validate(user)
