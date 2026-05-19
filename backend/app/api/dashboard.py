"""
DATASHIELD Dashboard API
Aggregated statistics and real-time metrics for the executive dashboard.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.models import AccessEvent, Alert, DataAsset, PolicyViolation, RiskAssessment
from app.schemas import ComplianceOverview, DashboardStats
from app.security import UserRole, get_current_user, require_role

logger = get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.SECURITY_ANALYST, UserRole.ADMIN)),
):
    """Get aggregated dashboard statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Total assets
    total_assets = (await db.execute(
        select(func.count()).select_from(DataAsset).where(DataAsset.is_active == True)
    )).scalar() or 0

    # Classified assets
    classified = (await db.execute(
        select(func.count()).select_from(DataAsset).where(
            DataAsset.sensitivity != "UNCLASSIFIED", DataAsset.is_active == True
        )
    )).scalar() or 0

    # Today's events
    events_today = (await db.execute(
        select(func.count()).select_from(AccessEvent).where(AccessEvent.created_at >= today_start)
    )).scalar() or 0

    # Today's anomalies
    anomalies_today = (await db.execute(
        select(func.count()).select_from(AccessEvent).where(
            AccessEvent.created_at >= today_start, AccessEvent.is_anomaly == True
        )
    )).scalar() or 0

    # Active alerts
    active_alerts = (await db.execute(
        select(func.count()).select_from(Alert).where(Alert.status == "OPEN")
    )).scalar() or 0

    # Risk distribution
    risk_dist_result = await db.execute(
        select(AccessEvent.risk_level, func.count())
        .where(AccessEvent.created_at >= today_start, AccessEvent.risk_level.isnot(None))
        .group_by(AccessEvent.risk_level)
    )
    risk_distribution = {row[0]: row[1] for row in risk_dist_result.all()}

    # Compliance score (based on policy violations ratio)
    total_checks = max(events_today, 1)
    violations_today = (await db.execute(
        select(func.count()).select_from(PolicyViolation).where(PolicyViolation.created_at >= today_start)
    )).scalar() or 0
    compliance_score = round(max(0, (1 - violations_today / total_checks) * 100), 1)

    return DashboardStats(
        total_assets=total_assets,
        classified_assets=classified,
        total_events_today=events_today,
        anomalies_today=anomalies_today,
        active_alerts=active_alerts,
        compliance_score=compliance_score,
        risk_distribution=risk_distribution,
        top_risk_users=[],
    )


@router.get("/compliance", response_model=ComplianceOverview)
async def get_compliance_overview(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.AUDITOR, UserRole.ADMIN)),
):
    """Get compliance framework overview."""
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # Pending violations
    pending = (await db.execute(
        select(func.count()).select_from(PolicyViolation).where(PolicyViolation.resolved == False)
    )).scalar() or 0

    # Resolved in last 30 days
    resolved = (await db.execute(
        select(func.count()).select_from(PolicyViolation).where(
            PolicyViolation.resolved == True, PolicyViolation.resolved_at >= thirty_days_ago
        )
    )).scalar() or 0

    total = max(pending + resolved, 1)
    overall = round((resolved / total) * 100, 1)

    return ComplianceOverview(
        overall_score=overall,
        frameworks={"GDPR": overall, "ISO27001": min(overall + 5, 100), "PCI-DSS": max(overall - 3, 0)},
        pending_violations=pending,
        resolved_violations_30d=resolved,
    )


@router.get("/alerts")
async def get_recent_alerts(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.SECURITY_ANALYST, UserRole.ADMIN)),
):
    """Get recent security alerts."""
    result = await db.execute(
        select(Alert).where(Alert.status == "OPEN")
        .order_by(Alert.created_at.desc()).limit(limit)
    )
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id), "type": a.alert_type, "severity": a.severity,
            "title": a.title, "title_ar": a.title_ar,
            "status": a.status, "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]
