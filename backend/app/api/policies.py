"""
DATASHIELD Policy Enforcement API
Governance policy CRUD and real-time access control decisions.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.models import DataAsset, GovernancePolicy, PolicyViolation
from app.schemas import (
    PaginatedResponse, PolicyCheckRequest, PolicyCheckResponse,
    PolicyCreate, PolicyResponse,
)
from app.security import UserRole, compute_audit_hash, get_current_user, require_role

logger = get_logger(__name__)
router = APIRouter(prefix="/policies", tags=["Policy Enforcement"])


@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    body: PolicyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.DATA_STEWARD, UserRole.ADMIN)),
):
    """Create a new governance policy."""
    policy = GovernancePolicy(
        name=body.name, name_ar=body.name_ar,
        description=body.description, description_ar=body.description_ar,
        policy_type=body.policy_type, severity=body.severity,
        conditions=body.conditions, actions=body.actions,
        created_by=UUID(current_user["sub"]),
        tenant_id=UUID(current_user["tenant_id"]) if current_user.get("tenant_id") else None,
        compliance_frameworks=body.compliance_frameworks,
    )
    db.add(policy)
    await db.flush()
    logger.info("policy_created", policy_id=str(policy.id), name=policy.name, type=policy.policy_type)
    return policy


@router.get("/", response_model=PaginatedResponse)
async def list_policies(
    policy_type: Optional[str] = None,
    is_active: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List governance policies."""
    query = select(GovernancePolicy).where(GovernancePolicy.is_active == is_active)
    if policy_type:
        query = query.where(GovernancePolicy.policy_type == policy_type)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    query = query.order_by(GovernancePolicy.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    policies = result.scalars().all()

    return PaginatedResponse(
        items=[PolicyResponse.model_validate(p) for p in policies],
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("/check", response_model=PolicyCheckResponse)
async def check_policy(
    body: PolicyCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Real-time policy check for an access request.
    Evaluates all active policies against the request context.
    """
    result = await db.execute(
        select(GovernancePolicy).where(
            GovernancePolicy.is_active == True,
            GovernancePolicy.policy_type == "ACCESS",
        )
    )
    policies = result.scalars().all()

    # Get asset sensitivity
    asset_result = await db.execute(select(DataAsset).where(DataAsset.id == body.asset_id))
    asset = asset_result.scalar_one_or_none()
    asset_sensitivity = asset.sensitivity if asset else "UNCLASSIFIED"

    for policy in policies:
        conditions = policy.conditions
        # Evaluate policy conditions
        if _evaluate_conditions(conditions, body, asset_sensitivity):
            # Policy violated
            violation = PolicyViolation(
                policy_id=policy.id, user_id=body.user_id,
                violation_type=body.action, severity=policy.severity,
                details={
                    "user_role": body.user_role, "asset_sensitivity": asset_sensitivity,
                    "risk_score": body.risk_score,
                },
                action_taken="BLOCKED",
            )
            db.add(violation)
            logger.warning(
                "policy_violation_detected",
                policy_id=str(policy.id), user_id=str(body.user_id),
                action=body.action, severity=policy.severity,
            )
            return PolicyCheckResponse(
                allowed=False,
                reason=f"POLICY_VIOLATION: {policy.name}",
                policy_id_triggered=policy.id,
            )

    return PolicyCheckResponse(allowed=True)


def _evaluate_conditions(conditions: dict, request: PolicyCheckRequest, sensitivity: str) -> bool:
    """Evaluate policy conditions against the request context."""
    # Check sensitivity restrictions
    if "blocked_sensitivities" in conditions:
        if sensitivity in conditions["blocked_sensitivities"]:
            if request.user_role in conditions.get("restricted_roles", []):
                return True

    # Check risk score thresholds
    if "max_risk_score" in conditions:
        if request.risk_score > conditions["max_risk_score"]:
            return True

    # Check action restrictions
    if "blocked_actions" in conditions:
        if request.action in conditions["blocked_actions"]:
            if request.user_role in conditions.get("restricted_roles", []):
                return True

    return False
