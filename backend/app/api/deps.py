"""FastAPI dependencies for control-room authentication."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.models import UserModel

_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthUser:
    id: str
    username: str
    full_name: str
    role: str
    organization: str
    unit: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_operator(self) -> bool:
        return self.role in {"operator", "admin"}


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
    token: str | None = Query(
        default=None,
        description="JWT for media elements (<video>/<img>) that cannot send Authorization headers",
    ),
) -> AuthUser:
    if not settings.auth_required:
        return AuthUser(
            id="dev",
            username="dev.admin",
            full_name="Dev Bypass Admin",
            role="admin",
            organization="CrowdPulse Dev",
            unit="Local",
        )

    raw: str | None = None
    if creds is not None and creds.scheme.lower() == "bearer" and creds.credentials:
        raw = creds.credentials
    elif token:
        raw = token

    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Sign in at the CrowdPulse control-room login.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    result = await db.execute(select(UserModel).where(UserModel.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive or not found")

    return AuthUser(
        id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        organization=user.organization,
        unit=user.unit,
    )


async def require_operator(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role not in {"operator", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Control-room operator or admin access required.",
        )
    return user


async def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required (CCTV ingest / system controls).",
        )
    return user
