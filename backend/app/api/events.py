"""
DATASHIELD Access Events API
Real-time data access event ingestion with risk scoring and audit logging.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.models import AccessEvent, AuditLog, DataAsset
from app.schemas import AccessEventCreate, AccessEventResponse, PaginatedResponse
from app.security import UserRole, compute_audit_hash, get_current_user, require_role

logger = get_logger(__name__)
router = APIRouter(prefix="/tracking", tags=["Access Tracking"])


@router.post("/events", response_model=AccessEventResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_access_event(
    request: Request,
    body: AccessEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Ingest a real-time data access event.
    The event is stored, queued for risk scoring, and audited.
    """
    trace_id = getattr(request.state, "trace_id", "no-trace")

    # Verify asset exists
    asset = await db.execute(select(DataAsset).where(DataAsset.id == body.asset_id))
    if not asset.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Data asset not found")

    # Compute query hash for deduplication
    query_hash = None
    if body.query_text:
        query_hash = hashlib.sha256(body.query_text.encode()).hexdigest()

    event = AccessEvent(
        trace_id=trace_id,
        user_id=body.user_id,
        asset_id=body.asset_id,
        action=body.action,
        query_text=body.query_text,
        query_hash=query_hash,
        ip_address=body.ip_address,
        user_agent=body.user_agent,
        rows_affected=body.rows_affected,
        session_id=body.session_id,
    )
    db.add(event)
    await db.flush()

    # Create immutable audit log entry
    audit = AuditLog(
        trace_id=trace_id,
        event_type="DATA_ACCESS",
        actor_id=str(body.user_id),
        action=body.action,
        resource_type="DATA_ASSET",
        resource_id=str(body.asset_id),
        details={"ip": body.ip_address, "query_hash": query_hash},
        ip_address=body.ip_address,
        status="RECORDED",
        chain_hash=compute_audit_hash(f"{body.action}:{body.asset_id}:{body.user_id}"),
    )
    db.add(audit)

    logger.info(
        "access_event_ingested",
        event_id=str(event.id), trace_id=trace_id,
        user_id=str(body.user_id), asset_id=str(body.asset_id),
        action=body.action,
    )

    return event


@router.get("/events", response_model=PaginatedResponse)
async def list_access_events(
    user_id: Optional[UUID] = None,
    asset_id: Optional[UUID] = None,
    action: Optional[str] = None,
    risk_level: Optional[str] = None,
    anomalies_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.SECURITY_ANALYST, UserRole.ADMIN)),
):
    """Query access events with filtering and pagination."""
    query = select(AccessEvent)

    if user_id:
        query = query.where(AccessEvent.user_id == user_id)
    if asset_id:
        query = query.where(AccessEvent.asset_id == asset_id)
    if action:
        query = query.where(AccessEvent.action == action)
    if risk_level:
        query = query.where(AccessEvent.risk_level == risk_level)
    if anomalies_only:
        query = query.where(AccessEvent.is_anomaly == True)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(AccessEvent.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    events = result.scalars().all()

    return PaginatedResponse(
        items=[AccessEventResponse.model_validate(e) for e in events],
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/events/{event_id}", response_model=AccessEventResponse)
async def get_access_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific access event by ID."""
    result = await db.execute(select(AccessEvent).where(AccessEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event
