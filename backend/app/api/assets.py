"""
DATASHIELD Data Assets API
CRUD operations for enterprise data asset management.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.models import DataAsset
from app.schemas import DataAssetCreate, DataAssetResponse, PaginatedResponse
from app.security import UserRole, get_current_user, require_role

logger = get_logger(__name__)
router = APIRouter(prefix="/assets", tags=["Data Assets"])


@router.post("/", response_model=DataAssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    body: DataAssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.DATA_STEWARD, UserRole.ADMIN)),
):
    """Register a new data asset for governance tracking."""
    asset = DataAsset(
        name=body.name, name_ar=body.name_ar, description=body.description,
        system_type=body.system_type, system_name=body.system_name,
        schema_name=body.schema_name, table_name=body.table_name,
        owner_id=UUID(current_user["sub"]),
        tenant_id=UUID(current_user["tenant_id"]) if current_user.get("tenant_id") else None,
    )
    db.add(asset)
    await db.flush()
    logger.info("asset_created", asset_id=str(asset.id), name=asset.name)
    return asset


@router.get("/", response_model=PaginatedResponse)
async def list_assets(
    sensitivity: Optional[str] = None,
    system_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List data assets with filtering."""
    query = select(DataAsset).where(DataAsset.is_active == True)
    if sensitivity:
        query = query.where(DataAsset.sensitivity == sensitivity)
    if system_type:
        query = query.where(DataAsset.system_type == system_type)
    if search:
        query = query.where(DataAsset.name.ilike(f"%{search}%"))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(DataAsset.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    assets = result.scalars().all()

    return PaginatedResponse(
        items=[DataAssetResponse.model_validate(a) for a in assets],
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{asset_id}", response_model=DataAssetResponse)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific data asset."""
    result = await db.execute(select(DataAsset).where(DataAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset
