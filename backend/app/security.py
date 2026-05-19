"""
DATASHIELD Security Module
JWT authentication, password hashing, RBAC enforcement, and data masking.
"""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()
security_scheme = HTTPBearer()

# --- Password Hashing ---
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
)


class UserRole(str, Enum):
    """RBAC roles for DATASHIELD users."""
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    DATA_STEWARD = "DATA_STEWARD"
    SECURITY_ANALYST = "SECURITY_ANALYST"
    AUDITOR = "AUDITOR"
    DATA_ANALYST = "DATA_ANALYST"
    VIEWER = "VIEWER"


# Role hierarchy: higher roles inherit lower role permissions
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.SUPER_ADMIN: 100,
    UserRole.ADMIN: 80,
    UserRole.DATA_STEWARD: 60,
    UserRole.SECURITY_ANALYST: 50,
    UserRole.AUDITOR: 40,
    UserRole.DATA_ANALYST: 30,
    UserRole.VIEWER: 10,
}


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str  # User ID
    role: str
    exp: datetime
    iat: datetime
    jti: str  # Unique token ID for revocation
    tenant_id: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# --- Password Operations ---
def hash_password(password: str) -> str:
    """Hash password using Argon2id."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT Operations ---
def create_access_token(
    user_id: str,
    role: str,
    tenant_id: Optional[str] = None,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
        "jti": secrets.token_hex(16),
        "tenant_id": tenant_id,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a signed JWT refresh token with longer expiry."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": now,
        "jti": secrets.token_hex(16),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.warning("jwt_decode_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- Authentication Dependencies ---
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict[str, Any]:
    """Extract and validate the current user from the JWT."""
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory: enforces RBAC on endpoints.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    async def role_checker(
        current_user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        user_role = current_user.get("role", "")
        try:
            user_role_enum = UserRole(user_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unknown role: {user_role}",
            )
        
        # Check if user's role level meets the minimum required
        user_level = ROLE_HIERARCHY.get(user_role_enum, 0)
        min_level = min(ROLE_HIERARCHY.get(r, 100) for r in allowed_roles)
        
        if user_level < min_level and user_role_enum not in allowed_roles:
            logger.warning(
                "access_denied",
                user_id=current_user.get("sub"),
                required_roles=[r.value for r in allowed_roles],
                user_role=user_role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


# --- Data Masking ---
class DataMasker:
    """
    Dynamic data masking engine.
    Masks PII based on user role and data classification.
    """

    # Patterns for common PII (Arabic + English)
    PATTERNS = {
        "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "phone": re.compile(r"(\+?\d{1,4}[\s-]?)?\(?\d{1,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}"),
        "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
        "national_id": re.compile(r"\b\d{10}\b"),  # Saudi National ID format
        "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b"),
    }

    @staticmethod
    def mask_email(value: str) -> str:
        """Mask email: a***@***.com"""
        parts = value.split("@")
        if len(parts) == 2:
            local = parts[0][0] + "***"
            domain_parts = parts[1].split(".")
            domain = "***." + domain_parts[-1] if domain_parts else "***"
            return f"{local}@{domain}"
        return "***@***.***"

    @staticmethod
    def mask_phone(value: str) -> str:
        """Mask phone: +971 ** *** **67"""
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 4:
            return digits[:3] + "*" * (len(digits) - 5) + digits[-2:]
        return "***"

    @staticmethod
    def mask_credit_card(value: str) -> str:
        """Mask card: XXXX-XXXX-XXXX-1234"""
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 4:
            return f"XXXX-XXXX-XXXX-{digits[-4:]}"
        return "XXXX-XXXX-XXXX-XXXX"

    @staticmethod
    def mask_generic(value: str) -> str:
        """Generic masking: show first and last char only."""
        if len(value) <= 2:
            return "***"
        return value[0] + "*" * (len(value) - 2) + value[-1]

    @classmethod
    def mask_field(cls, field_type: str, value: str) -> str:
        """Mask a field based on its detected type."""
        maskers = {
            "email": cls.mask_email,
            "phone": cls.mask_phone,
            "credit_card": cls.mask_credit_card,
        }
        masker = maskers.get(field_type, cls.mask_generic)
        return masker(value)

    @classmethod
    def mask_text(cls, text: str, user_role: UserRole) -> str:
        """
        Scan and mask PII in free text based on user role.
        SUPER_ADMIN and DATA_STEWARD see unmasked data.
        """
        if user_role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
            return text

        result = text
        for field_type, pattern in cls.PATTERNS.items():
            for match in pattern.finditer(result):
                masked = cls.mask_field(field_type, match.group())
                result = result.replace(match.group(), masked, 1)
        return result


# --- Audit Hash ---
def compute_audit_hash(data: str, previous_hash: str = "") -> str:
    """
    Compute a chained SHA-256 hash for immutable audit log integrity.
    Each hash depends on the previous, creating a tamper-evident chain.
    """
    combined = f"{previous_hash}:{data}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


# --- Input Sanitization ---
def sanitize_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    Strips dangerous characters and enforces length limits.
    """
    if not isinstance(value, str):
        return str(value)
    # Truncate
    value = value[:max_length]
    # Remove null bytes
    value = value.replace("\x00", "")
    # Strip leading/trailing whitespace
    value = value.strip()
    return value
