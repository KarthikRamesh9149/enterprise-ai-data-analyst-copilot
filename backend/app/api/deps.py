from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.rbac import has_permission
from app.core.security import decode_token
from app.db.models import AuditLog, User
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user = db.get(User, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_permission(permission: str) -> Callable:
    def dependency(
        request: Request,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        if not has_permission(user.role, permission):
            db.add(
                AuditLog(
                    user_id=user.id,
                    action="permission_denied",
                    resource_type="permission",
                    resource_id=permission,
                    event_metadata={"role": user.role, "path": str(request.url.path)},
                )
            )
            db.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission")
        return user

    return dependency


def request_context(
    request: Request,
    user_agent: str | None = Header(default=None),
) -> dict:
    client = request.client.host if request.client else None
    return {"ip_address": client, "user_agent": user_agent}
