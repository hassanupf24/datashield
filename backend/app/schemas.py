"""
DATASHIELD Pydantic Schemas
Request/Response validation models for all API endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================
# AUTH SCHEMAS
# ============================================================
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str = Field(..., max_length=255)
    full_name_ar: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=128)
    role: str = "VIEWER"
    department: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str
    full_name_ar: Optional[str] = None
    role: str
    department: Optional[str] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# ACCESS EVENT SCHEMAS
# ============================================================
class AccessEventCreate(BaseModel):
    user_id: UUID
    asset_id: UUID
    action: Literal["READ", "WRITE", "DELETE", "EXPORT"]
    query_text: Optional[str] = None
    ip_address: str
    user_agent: Optional[str] = None
    rows_affected: Optional[int] = None
    session_id: Optional[str] = None

class AccessEventResponse(BaseModel):
    id: UUID
    trace_id: str
    user_id: UUID
    asset_id: UUID
    action: str
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    is_anomaly: bool
    policy_action: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# CLASSIFICATION SCHEMAS
# ============================================================
class ClassificationRequest(BaseModel):
    asset_id: UUID
    sample_data: List[str] = Field(..., min_length=1, max_length=100)
    language: Literal["en", "ar"] = "en"

class ClassificationResponse(BaseModel):
    asset_id: UUID
    classification: str
    confidence_score: float
    detected_entities: List[str]
    explanation: dict[str, Any]
    model_version: str


# ============================================================
# RISK SCHEMAS
# ============================================================
class RiskEvaluationRequest(BaseModel):
    event_id: UUID
    user_id: UUID
    asset_id: UUID
    action: str

class RiskEvaluationResponse(BaseModel):
    event_id: UUID
    risk_score: float
    risk_level: str
    is_anomaly: bool
    factors: List[dict[str, Any]]
    recommendation: str


# ============================================================
# POLICY SCHEMAS
# ============================================================
class PolicyCreate(BaseModel):
    name: str = Field(..., max_length=255)
    name_ar: Optional[str] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None
    policy_type: Literal["ACCESS", "MASKING", "RETENTION", "CLASSIFICATION"]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    conditions: dict[str, Any]
    actions: dict[str, Any]
    compliance_frameworks: List[str] = []

class PolicyResponse(BaseModel):
    id: UUID
    name: str
    name_ar: Optional[str] = None
    policy_type: str
    severity: str
    is_active: bool
    compliance_frameworks: List[str]
    created_at: datetime
    model_config = {"from_attributes": True}

class PolicyCheckRequest(BaseModel):
    user_id: UUID
    user_role: str
    asset_id: UUID
    action: str
    risk_score: int = 0

class PolicyCheckResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    policy_id_triggered: Optional[UUID] = None


# ============================================================
# AUDIT SCHEMAS
# ============================================================
class AuditLogResponse(BaseModel):
    id: UUID
    trace_id: str
    event_type: str
    actor_id: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}

class AuditQueryParams(BaseModel):
    user_id: Optional[str] = None
    event_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    page_size: int = 50


# ============================================================
# DATA ASSET SCHEMAS
# ============================================================
class DataAssetCreate(BaseModel):
    name: str = Field(..., max_length=255)
    name_ar: Optional[str] = None
    description: Optional[str] = None
    system_type: str
    system_name: str
    schema_name: Optional[str] = None
    table_name: Optional[str] = None

class DataAssetResponse(BaseModel):
    id: UUID
    name: str
    name_ar: Optional[str] = None
    system_type: str
    system_name: str
    sensitivity: str
    classification_confidence: Optional[float] = None
    tags: List[str]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ============================================================
# LINEAGE SCHEMAS
# ============================================================
class LineageCreate(BaseModel):
    source_asset_id: UUID
    target_asset_id: UUID
    transformation_type: str
    transformation_details: dict[str, Any] = {}
    pipeline_name: Optional[str] = None

class LineageResponse(BaseModel):
    id: UUID
    source_asset_id: UUID
    target_asset_id: UUID
    transformation_type: str
    pipeline_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

class LineageGraphResponse(BaseModel):
    nodes: List[dict[str, Any]]
    edges: List[dict[str, Any]]


# ============================================================
# ALERT SCHEMAS
# ============================================================
class AlertResponse(BaseModel):
    id: UUID
    alert_type: str
    severity: str
    title: str
    title_ar: Optional[str] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ============================================================
# DASHBOARD SCHEMAS
# ============================================================
class DashboardStats(BaseModel):
    total_assets: int
    classified_assets: int
    total_events_today: int
    anomalies_today: int
    active_alerts: int
    compliance_score: float
    risk_distribution: dict[str, int]
    top_risk_users: List[dict[str, Any]]

class ComplianceOverview(BaseModel):
    overall_score: float
    frameworks: dict[str, float]  # e.g. {"GDPR": 92.5, "ISO27001": 88.0}
    pending_violations: int
    resolved_violations_30d: int


# ============================================================
# GENERIC
# ============================================================
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    redis: str
    uptime_seconds: float
