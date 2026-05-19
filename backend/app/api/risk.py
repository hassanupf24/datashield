"""
DATASHIELD Risk Assessment API
Real-time risk scoring and anomaly detection endpoints.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.risk_engine import risk_engine
from app.database import get_db
from app.logging_config import get_logger
from app.models import AccessEvent, Alert, DataAsset, RiskAssessment, User
from app.schemas import RiskEvaluationRequest, RiskEvaluationResponse
from app.security import UserRole, get_current_user, require_role

logger = get_logger(__name__)
router = APIRouter(prefix="/risk", tags=["Risk Scoring"])


@router.post("/evaluate", response_model=RiskEvaluationResponse)
async def evaluate_risk(
    body: RiskEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Evaluate the risk of a data access event.
    Returns risk score with SHAP-style explainable factors.
    """
    # Get asset sensitivity
    asset_result = await db.execute(select(DataAsset).where(DataAsset.id == body.asset_id))
    asset = asset_result.scalar_one_or_none()
    asset_sensitivity = asset.sensitivity if asset else "UNCLASSIFIED"

    # Get user role
    user_result = await db.execute(select(User).where(User.id == body.user_id))
    user = user_result.scalar_one_or_none()
    user_role = user.role if user else "VIEWER"

    # Get event details
    event_result = await db.execute(select(AccessEvent).where(AccessEvent.id == body.event_id))
    event = event_result.scalar_one_or_none()

    ip_address = event.ip_address if event else ""
    rows_affected = event.rows_affected if event else None
    query_text = event.query_text if event else None

    # Run risk evaluation
    result = risk_engine.evaluate(
        user_id=body.user_id,
        asset_id=body.asset_id,
        action=body.action,
        ip_address=ip_address,
        rows_affected=rows_affected,
        asset_sensitivity=asset_sensitivity,
        user_role=user_role,
        query_text=query_text,
    )

    # Store assessment
    assessment = RiskAssessment(
        event_id=body.event_id,
        user_id=body.user_id,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        is_anomaly=result["is_anomaly"],
        factors=result["factors"],
        model_version=result["model_version"],
        recommendation=result["recommendation"],
    )
    db.add(assessment)

    # Update event with risk info
    if event:
        event.risk_score = result["risk_score"]
        event.risk_level = result["risk_level"]
        event.is_anomaly = result["is_anomaly"]

    # Create alert for high-risk events
    if result["is_anomaly"]:
        alert = Alert(
            alert_type="ANOMALY",
            severity=result["risk_level"],
            title=f"Anomalous access detected: {body.action} on asset",
            title_ar=f"اكتشاف وصول غير طبيعي: {body.action}",
            description=f"User {body.user_id} risk score: {result['risk_score']}",
            description_ar=f"درجة خطورة المستخدم: {result['risk_score']}",
            source_event_id=body.event_id,
            tenant_id=UUID(current_user["tenant_id"]) if current_user.get("tenant_id") else None,
        )
        db.add(alert)

    return RiskEvaluationResponse(
        event_id=body.event_id,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        is_anomaly=result["is_anomaly"],
        factors=result["factors"],
        recommendation=result["recommendation"],
    )
