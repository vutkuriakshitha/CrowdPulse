"""Control-room authentication for Telangana police / stadium ops."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthUser, get_current_user
from app.core.security import create_access_token, verify_password
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.models import UserModel

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)


class UserOut(BaseModel):
    username: str
    full_name: str
    role: str
    organization: str
    unit: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserModel).where(UserModel.username == body.username.strip()))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(
        subject=user.username,
        role=user.role,
        full_name=user.full_name,
        organization=user.organization,
        unit=user.unit,
    )
    return LoginResponse(
        access_token=token,
        user=UserOut(
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            organization=user.organization,
            unit=user.unit,
        ),
    )


@router.get("/me", response_model=UserOut)
async def me(user: AuthUser = Depends(get_current_user)):
    return UserOut(
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        organization=user.organization,
        unit=user.unit,
    )
