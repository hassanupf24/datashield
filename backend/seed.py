"""
DATASHIELD Database Seeder
Creates initial admin user, sample tenant, default policies, and demo data.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import async_session_factory, init_db
from app.logging_config import get_logger, setup_logging
from app.models import (
    AccessEvent, Alert, DataAsset, DataLineage,
    GovernancePolicy, Tenant, User,
)
from app.security import compute_audit_hash, hash_password

logger = get_logger(__name__)
settings = get_settings()


async def seed_database():
    """Seed the database with initial data."""
    setup_logging(log_level="INFO", log_format="console")
    await init_db()

    async with async_session_factory() as db:
        # Check if already seeded
        existing = await db.execute(select(User).limit(1))
        if existing.scalar_one_or_none():
            logger.info("database_already_seeded")
            return

        logger.info("seeding_database")

        # --- Tenant ---
        tenant = Tenant(
            name="DATASHIELD Corp",
            name_ar="شركة داتا شيلد",
            domain="datashield.io",
            settings={"timezone": "Asia/Riyadh", "language": "ar"},
        )
        db.add(tenant)
        await db.flush()

        # --- Users ---
        users_data = [
            {"username": "admin", "email": "admin@datashield.io", "full_name": "System Admin",
             "full_name_ar": "مدير النظام", "role": "SUPER_ADMIN", "department": "IT"},
            {"username": "steward", "email": "steward@datashield.io", "full_name": "Data Steward",
             "full_name_ar": "مسؤول البيانات", "role": "DATA_STEWARD", "department": "Governance"},
            {"username": "analyst", "email": "analyst@datashield.io", "full_name": "Security Analyst",
             "full_name_ar": "محلل أمني", "role": "SECURITY_ANALYST", "department": "Security"},
            {"username": "auditor", "email": "auditor@datashield.io", "full_name": "Compliance Auditor",
             "full_name_ar": "مدقق الامتثال", "role": "AUDITOR", "department": "Compliance"},
            {"username": "viewer", "email": "viewer@datashield.io", "full_name": "Report Viewer",
             "full_name_ar": "مشاهد التقارير", "role": "VIEWER", "department": "Management"},
        ]

        users = []
        for ud in users_data:
            user = User(
                **ud,
                hashed_password=hash_password("DataShield@2026"),
                tenant_id=tenant.id,
            )
            db.add(user)
            users.append(user)
        await db.flush()

        # --- Data Assets ---
        assets_data = [
            {"name": "Customer Database", "name_ar": "قاعدة بيانات العملاء",
             "system_type": "POSTGRES", "system_name": "core-banking",
             "schema_name": "public", "table_name": "customers", "sensitivity": "CONFIDENTIAL"},
            {"name": "Transaction Ledger", "name_ar": "سجل المعاملات",
             "system_type": "POSTGRES", "system_name": "core-banking",
             "schema_name": "finance", "table_name": "transactions", "sensitivity": "REGULATED"},
            {"name": "Employee Records", "name_ar": "سجلات الموظفين",
             "system_type": "POSTGRES", "system_name": "hr-system",
             "schema_name": "hr", "table_name": "employees", "sensitivity": "HIGHLY_SENSITIVE"},
            {"name": "Marketing Analytics", "name_ar": "تحليلات التسويق",
             "system_type": "S3", "system_name": "data-lake",
             "schema_name": "analytics", "table_name": "campaign_metrics", "sensitivity": "INTERNAL"},
            {"name": "Public Reports", "name_ar": "التقارير العامة",
             "system_type": "S3", "system_name": "report-store",
             "schema_name": None, "table_name": "annual_reports", "sensitivity": "PUBLIC"},
            {"name": "KYC Documents", "name_ar": "وثائق اعرف عميلك",
             "system_type": "S3", "system_name": "compliance-vault",
             "schema_name": None, "table_name": "kyc_docs", "sensitivity": "REGULATED"},
        ]

        assets = []
        for ad in assets_data:
            asset = DataAsset(**ad, owner_id=users[1].id, tenant_id=tenant.id)
            db.add(asset)
            assets.append(asset)
        await db.flush()

        # --- Data Lineage ---
        lineage_data = [
            (0, 3, "ETL", "data-pipeline-v1"),  # Customer DB → Marketing Analytics
            (1, 3, "AGGREGATE", "finance-pipeline"),  # Transactions → Marketing
            (0, 5, "COPY", "kyc-pipeline"),  # Customer DB → KYC
        ]
        for src_idx, tgt_idx, transform, pipeline in lineage_data:
            lineage = DataLineage(
                source_asset_id=assets[src_idx].id,
                target_asset_id=assets[tgt_idx].id,
                transformation_type=transform,
                pipeline_name=pipeline,
                last_executed=datetime.now(timezone.utc),
            )
            db.add(lineage)

        # --- Governance Policies ---
        policies = [
            GovernancePolicy(
                name="Block Export of Regulated Data",
                name_ar="منع تصدير البيانات المنظمة",
                description="Prevent non-admin users from exporting regulated data",
                description_ar="منع المستخدمين غير المسؤولين من تصدير البيانات المنظمة",
                policy_type="ACCESS", severity="CRITICAL",
                conditions={
                    "blocked_sensitivities": ["REGULATED", "HIGHLY_SENSITIVE"],
                    "restricted_roles": ["DATA_ANALYST", "VIEWER"],
                    "blocked_actions": ["EXPORT", "DELETE"],
                },
                actions={"action": "BLOCK", "notify": ["SECURITY_ANALYST"]},
                tenant_id=tenant.id, created_by=users[0].id,
                compliance_frameworks=["GDPR", "PCI-DSS", "ISO27001"],
            ),
            GovernancePolicy(
                name="Flag High Risk Score Access",
                name_ar="تنبيه الوصول عالي الخطورة",
                description="Flag any access with risk score above 80",
                description_ar="تنبيه أي وصول بدرجة خطورة أعلى من 80",
                policy_type="ACCESS", severity="HIGH",
                conditions={"max_risk_score": 80},
                actions={"action": "FLAG", "notify": ["SECURITY_ANALYST", "ADMIN"]},
                tenant_id=tenant.id, created_by=users[0].id,
                compliance_frameworks=["ISO27001"],
            ),
        ]
        for p in policies:
            db.add(p)

        # --- Sample Alerts ---
        alerts = [
            Alert(
                alert_type="ANOMALY", severity="HIGH",
                title="Unusual data export detected",
                title_ar="اكتشاف تصدير بيانات غير عادي",
                description="User attempted bulk export of customer records at 2AM",
                description_ar="محاولة المستخدم تصدير سجلات العملاء بالجملة في الساعة 2 صباحاً",
                status="OPEN", tenant_id=tenant.id,
            ),
            Alert(
                alert_type="POLICY_VIOLATION", severity="CRITICAL",
                title="Regulated data access violation",
                title_ar="انتهاك الوصول للبيانات المنظمة",
                description="Analyst role attempted DELETE on transaction ledger",
                description_ar="محاولة دور المحلل حذف سجل المعاملات",
                status="OPEN", tenant_id=tenant.id,
            ),
        ]
        for a in alerts:
            db.add(a)

        await db.commit()
        logger.info("database_seeded_successfully", users=len(users), assets=len(assets))


if __name__ == "__main__":
    asyncio.run(seed_database())
