"""
DATASHIELD Audit Logs API
Immutable audit log querying with cryptographic chain verification.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.models import AuditLog
from app.schemas import AuditLogResponse, PaginatedResponse
from app.security import UserRole, require_role

logger = get_logger(__name__)
router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/logs", response_model=PaginatedResponse)
async def query_audit_logs(
    actor_id: Optional[str] = None,
    event_type: Optional[str] = None,
    action: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.AUDITOR, UserRole.ADMIN)),
):
    """
    Query immutable audit logs with filtering.
    Only AUDITOR and ADMIN roles can access.
    """
    query = select(AuditLog)

    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if action:
        query = query.where(AuditLog.action == action)
    if status_filter:
        query = query.where(AuditLog.status == status_filter)
    if start_time:
        query = query.where(AuditLog.created_at >= start_time)
    if end_time:
        query = query.where(AuditLog.created_at <= end_time)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return PaginatedResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.AUDITOR, UserRole.ADMIN)),
):
    """Get a specific audit log entry."""
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    return log


@router.get("/verify-chain")
async def verify_audit_chain(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
):
    """
    Verify the cryptographic integrity of the audit chain.
    Returns whether the chain is intact or tampered.
    """
    query = select(AuditLog).order_by(AuditLog.created_at.asc())
    if start_time:
        query = query.where(AuditLog.created_at >= start_time)
    if end_time:
        query = query.where(AuditLog.created_at <= end_time)

    result = await db.execute(query)
    logs = result.scalars().all()

    if not logs:
        return {"status": "EMPTY", "message": "No logs in range", "verified_count": 0}

    broken_links = []
    for i in range(1, len(logs)):
        if logs[i].previous_hash and logs[i].previous_hash != logs[i - 1].chain_hash:
            broken_links.append({
                "log_id": str(logs[i].id),
                "expected_previous": logs[i - 1].chain_hash,
                "actual_previous": logs[i].previous_hash,
            })

    if broken_links:
        logger.critical("audit_chain_tampered", broken_count=len(broken_links))
        return {
            "status": "TAMPERED",
            "message": f"Chain integrity broken at {len(broken_links)} point(s)",
            "broken_links": broken_links,
            "verified_count": len(logs),
        }

    return {
        "status": "INTACT",
        "message": "Audit chain integrity verified",
        "verified_count": len(logs),
    }
