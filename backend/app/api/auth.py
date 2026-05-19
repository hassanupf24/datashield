"""
DATASHIELD Authentication API
Login, token refresh, user registration with full audit logging.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.models import AuditLog, User
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.security import (
    UserRole, compute_audit_hash, create_access_token,
    create_refresh_token, decode_token, get_current_user,
    hash_password, require_role, verify_password,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

MAX_LOGIN_ATTEMPTS = 5


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and issue JWT tokens."""
    result = await db.execute(
        select(User).where(User.username == body.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.is_locked = True
                logger.warning("account_locked", user_id=str(user.id))
        logger.warning("login_failed", username=body.username, ip=request.client.host)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account locked")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    # Reset failed attempts on success
    user.failed_login_attempts = 0
    user.last_login = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host

    access_token = create_access_token(
        user_id=str(user.id), role=user.role,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )
    refresh_token = create_refresh_token(user_id=str(user.id))

    # Audit log
    audit = AuditLog(
        trace_id=request.state.trace_id if hasattr(request.state, "trace_id") else "no-trace",
        event_type="AUTH_EVENT", actor_id=str(user.id), actor_role=user.role,
        action="LOGIN", status="SUCCESS", ip_address=request.client.host,
        chain_hash=compute_audit_hash(f"LOGIN:{user.id}"),
        details={"method": "password"},
    )
    db.add(audit)

    logger.info("login_success", user_id=str(user.id), role=user.role)

    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token,
        expires_in=1800,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
):
    """Register a new user (Admin only)."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email, username=body.username, full_name=body.full_name,
        full_name_ar=body.full_name_ar, hashed_password=hash_password(body.password),
        role=body.role, department=body.department,
    )
    db.add(user)
    await db.flush()

    logger.info("user_registered", user_id=str(user.id), role=user.role, by=current_user.get("sub"))
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current authenticated user profile."""
    result = await db.execute(select(User).where(User.id == UUID(current_user["sub"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token."""
    result = await db.execute(select(User).where(User.id == UUID(current_user["sub"])))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    access_token = create_access_token(
        user_id=str(user.id), role=user.role,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
    )
    refresh = create_refresh_token(user_id=str(user.id))
    return TokenResponse(access_token=access_token, refresh_token=refresh, expires_in=1800)
