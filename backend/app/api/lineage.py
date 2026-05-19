"""
DATASHIELD Data Lineage API
Graph-based data lineage tracking and impact analysis.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.logging_config import get_logger
from app.models import DataAsset, DataLineage
from app.schemas import LineageCreate, LineageGraphResponse, LineageResponse
from app.security import UserRole, get_current_user, require_role

logger = get_logger(__name__)
router = APIRouter(prefix="/lineage", tags=["Data Lineage"])


@router.post("/", response_model=LineageResponse, status_code=status.HTTP_201_CREATED)
async def create_lineage(
    body: LineageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.DATA_STEWARD, UserRole.ADMIN)),
):
    """Register a data lineage edge (source → target)."""
    # Verify both assets exist
    for asset_id in [body.source_asset_id, body.target_asset_id]:
        result = await db.execute(select(DataAsset).where(DataAsset.id == asset_id))
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found",
            )

    lineage = DataLineage(
        source_asset_id=body.source_asset_id,
        target_asset_id=body.target_asset_id,
        transformation_type=body.transformation_type,
        transformation_details=body.transformation_details,
        pipeline_name=body.pipeline_name,
    )
    db.add(lineage)
    await db.flush()
    logger.info(
        "lineage_created",
        source=str(body.source_asset_id), target=str(body.target_asset_id),
        type=body.transformation_type,
    )
    return lineage


@router.get("/graph/{asset_id}", response_model=LineageGraphResponse)
async def get_lineage_graph(
    asset_id: UUID,
    depth: int = 3,
    direction: str = "both",  # upstream, downstream, both
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the lineage graph for a specific asset.
    Returns nodes and edges for visualization.
    """
    visited = set()
    nodes = []
    edges = []

    async def traverse(current_id: UUID, current_depth: int):
        if current_depth > depth or current_id in visited:
            return
        visited.add(current_id)

        # Get asset info
        asset_result = await db.execute(select(DataAsset).where(DataAsset.id == current_id))
        asset = asset_result.scalar_one_or_none()
        if asset:
            nodes.append({
                "id": str(asset.id),
                "name": asset.name,
                "name_ar": asset.name_ar,
                "type": asset.system_type,
                "sensitivity": asset.sensitivity,
            })

        # Upstream (sources)
        if direction in ("upstream", "both"):
            upstream = await db.execute(
                select(DataLineage).where(DataLineage.target_asset_id == current_id, DataLineage.is_active == True)
            )
            for edge in upstream.scalars().all():
                edges.append({
                    "id": str(edge.id),
                    "source": str(edge.source_asset_id),
                    "target": str(edge.target_asset_id),
                    "type": edge.transformation_type,
                    "pipeline": edge.pipeline_name,
                })
                await traverse(edge.source_asset_id, current_depth + 1)

        # Downstream (targets)
        if direction in ("downstream", "both"):
            downstream = await db.execute(
                select(DataLineage).where(DataLineage.source_asset_id == current_id, DataLineage.is_active == True)
            )
            for edge in downstream.scalars().all():
                edges.append({
                    "id": str(edge.id),
                    "source": str(edge.source_asset_id),
                    "target": str(edge.target_asset_id),
                    "type": edge.transformation_type,
                    "pipeline": edge.pipeline_name,
                })
                await traverse(edge.target_asset_id, current_depth + 1)

    await traverse(asset_id, 0)

    return LineageGraphResponse(nodes=nodes, edges=edges)


@router.get("/impact/{asset_id}")
async def analyze_impact(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.DATA_STEWARD, UserRole.ADMIN)),
):
    """
    Blast radius analysis: if this asset is compromised,
    which downstream assets are affected?
    """
    graph = await get_lineage_graph(asset_id, depth=10, direction="downstream", db=db, current_user=current_user)

    sensitive_affected = [n for n in graph.nodes if n.get("sensitivity") in ("CONFIDENTIAL", "HIGHLY_SENSITIVE", "REGULATED")]

    return {
        "source_asset_id": str(asset_id),
        "total_affected_assets": len(graph.nodes) - 1,  # Exclude source
        "sensitive_assets_affected": len(sensitive_affected),
        "affected_assets": graph.nodes,
        "data_flows": graph.edges,
        "risk_level": "CRITICAL" if sensitive_affected else "LOW",
    }
