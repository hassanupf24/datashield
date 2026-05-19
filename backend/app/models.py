"""
DATASHIELD Database Models
Complete SQLAlchemy ORM models for all platform entities.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    full_name_ar = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="VIEWER")
    department = Column(String(100), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    tenant = relationship("Tenant", back_populates="users")
    access_events = relationship("AccessEvent", back_populates="user")
    __table_args__ = (Index("ix_users_role_tenant", "role", "tenant_id"),)


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    name_ar = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    users = relationship("User", back_populates="tenant")
    data_assets = relationship("DataAsset", back_populates="tenant")
    policies = relationship("GovernancePolicy", back_populates="tenant")


class DataAsset(Base):
    __tablename__ = "data_assets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    name_ar = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    system_type = Column(String(50), nullable=False)
    system_name = Column(String(255), nullable=False)
    schema_name = Column(String(255), nullable=True)
    table_name = Column(String(255), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    sensitivity = Column(String(50), default="UNCLASSIFIED")
    classification_confidence = Column(Float, nullable=True)
    classification_details = Column(JSONB, default=dict)
    tags = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    tenant = relationship("Tenant", back_populates="data_assets")
    access_events = relationship("AccessEvent", back_populates="asset")
    classifications = relationship("ClassificationResult", back_populates="asset")
    lineage_sources = relationship("DataLineage", back_populates="source_asset", foreign_keys="DataLineage.source_asset_id")
    lineage_targets = relationship("DataLineage", back_populates="target_asset", foreign_keys="DataLineage.target_asset_id")
    __table_args__ = (
        Index("ix_data_assets_sensitivity", "sensitivity"),
        UniqueConstraint("system_name", "schema_name", "table_name", name="uq_asset_location"),
    )


class ClassificationResult(Base):
    __tablename__ = "classification_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("data_assets.id"), nullable=False, index=True)
    classification = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    detected_entities = Column(JSONB, default=list)
    explanation = Column(JSONB, default=dict)
    model_version = Column(String(50), nullable=False)
    language = Column(String(10), default="en")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    asset = relationship("DataAsset", back_populates="classifications")


class AccessEvent(Base):
    __tablename__ = "access_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(50), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("data_assets.id"), nullable=False, index=True)
    action = Column(String(20), nullable=False)
    query_text = Column(Text, nullable=True)
    query_hash = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    rows_affected = Column(Integer, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True)
    is_anomaly = Column(Boolean, default=False)
    policy_action = Column(String(20), nullable=True)
    session_id = Column(String(100), nullable=True)
    event_metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="access_events")
    asset = relationship("DataAsset", back_populates="access_events")
    __table_args__ = (
        Index("ix_access_events_user_time", "user_id", "created_at"),
        Index("ix_access_events_risk", "risk_level", "is_anomaly"),
    )


class GovernancePolicy(Base):
    __tablename__ = "governance_policies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    name_ar = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    policy_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="MEDIUM")
    conditions = Column(JSONB, nullable=False)
    actions = Column(JSONB, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    compliance_frameworks = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    tenant = relationship("Tenant", back_populates="policies")
    violations = relationship("PolicyViolation", back_populates="policy")


class PolicyViolation(Base):
    __tablename__ = "policy_violations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("governance_policies.id"), nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("access_events.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    violation_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    details = Column(JSONB, default=dict)
    action_taken = Column(String(50), nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    policy = relationship("GovernancePolicy", back_populates="violations")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    actor_id = Column(String(100), nullable=False)
    actor_role = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSONB, default=dict)
    ip_address = Column(String(45), nullable=True)
    status = Column(String(20), nullable=False)
    chain_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        Index("ix_audit_logs_actor_time", "actor_id", "created_at"),
        Index("ix_audit_logs_event_type", "event_type", "created_at"),
    )


class DataLineage(Base):
    __tablename__ = "data_lineage"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_asset_id = Column(UUID(as_uuid=True), ForeignKey("data_assets.id"), nullable=False, index=True)
    target_asset_id = Column(UUID(as_uuid=True), ForeignKey("data_assets.id"), nullable=False, index=True)
    transformation_type = Column(String(50), nullable=False)
    transformation_details = Column(JSONB, default=dict)
    pipeline_name = Column(String(255), nullable=True)
    last_executed = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    source_asset = relationship("DataAsset", foreign_keys=[source_asset_id], back_populates="lineage_sources")
    target_asset = relationship("DataAsset", foreign_keys=[target_asset_id], back_populates="lineage_targets")
    __table_args__ = (
        UniqueConstraint("source_asset_id", "target_asset_id", "transformation_type", name="uq_lineage_edge"),
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("access_events.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    is_anomaly = Column(Boolean, default=False)
    factors = Column(JSONB, default=list)
    model_version = Column(String(50), nullable=False)
    recommendation = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    title_ar = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    source_event_id = Column(UUID(as_uuid=True), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="OPEN")
    resolution_notes = Column(Text, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    __table_args__ = (Index("ix_alerts_status_severity", "status", "severity"),)
