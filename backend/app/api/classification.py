"""
DATASHIELD Classification API
AI-powered data sensitivity classification endpoints.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import classifier
from app.database import get_db
from app.logging_config import get_logger
from app.models import ClassificationResult, DataAsset
from app.schemas import ClassificationRequest, ClassificationResponse
from app.security import UserRole, require_role

logger = get_logger(__name__)
router = APIRouter(prefix="/classification", tags=["AI Classification"])


@router.post("/analyze", response_model=ClassificationResponse)
async def classify_data(
    body: ClassificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.DATA_STEWARD, UserRole.ADMIN)),
):
    """
    Classify data samples using AI.
    Returns sensitivity level with explainable results.
    """
    # Verify asset exists
    result = await db.execute(select(DataAsset).where(DataAsset.id == body.asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    # Run classification
    classification = classifier.classify(
        sample_data=body.sample_data,
        language=body.language,
    )

    # Store result
    db_result = ClassificationResult(
        asset_id=body.asset_id,
        classification=classification["classification"],
        confidence_score=classification["confidence_score"],
        detected_entities=classification["detected_entities"],
        explanation=classification["explanation"],
        model_version=classification["model_version"],
        language=body.language,
    )
    db.add(db_result)

    # Update asset sensitivity
    if classification["confidence_score"] >= 0.7:
        asset.sensitivity = classification["classification"]
        asset.classification_confidence = classification["confidence_score"]
        asset.classification_details = classification["explanation"]

    logger.info(
        "classification_completed",
        asset_id=str(body.asset_id),
        classification=classification["classification"],
        confidence=classification["confidence_score"],
        entities=classification["detected_entities"],
    )

    return ClassificationResponse(
        asset_id=body.asset_id,
        classification=classification["classification"],
        confidence_score=classification["confidence_score"],
        detected_entities=classification["detected_entities"],
        explanation=classification["explanation"],
        model_version=classification["model_version"],
    )


@router.post("/batch")
async def classify_batch(
    requests: list[ClassificationRequest],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(UserRole.DATA_STEWARD, UserRole.ADMIN)),
):
    """Batch classify multiple data assets."""
    results = []
    for req in requests[:50]:  # Limit batch size
        try:
            classification = classifier.classify(
                sample_data=req.sample_data,
                language=req.language,
            )
            results.append({
                "asset_id": str(req.asset_id),
                "classification": classification["classification"],
                "confidence_score": classification["confidence_score"],
                "status": "SUCCESS",
            })
        except Exception as e:
            results.append({
                "asset_id": str(req.asset_id),
                "status": "ERROR",
                "error": str(e),
            })

    return {"results": results, "total": len(results)}
