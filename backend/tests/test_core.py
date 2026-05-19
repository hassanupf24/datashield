"""
DATASHIELD Test Suite
Tests for security, classification, risk scoring, and API endpoints.
"""
import pytest
from app.security import (
    DataMasker, UserRole, compute_audit_hash,
    hash_password, sanitize_input, verify_password,
)
from app.ai import DataClassifier
from app.ai.risk_engine import RiskScoringEngine
from uuid import uuid4


# ============================================================
# Security Tests
# ============================================================
class TestPasswordSecurity:
    def test_hash_and_verify(self):
        pwd = "TestPassword123!"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_hash_uniqueness(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # Argon2 uses random salts


class TestDataMasking:
    def test_mask_email(self):
        result = DataMasker.mask_email("john.doe@example.com")
        assert "john.doe" not in result
        assert "@" in result
        assert result.endswith(".com")

    def test_mask_phone(self):
        result = DataMasker.mask_phone("+971 50 123 4567")
        assert "123" not in result

    def test_mask_credit_card(self):
        result = DataMasker.mask_credit_card("4111 1111 1111 1234")
        assert result == "XXXX-XXXX-XXXX-1234"

    def test_role_based_masking(self):
        text = "Email: user@test.com Phone: +971501234567"
        masked = DataMasker.mask_text(text, UserRole.VIEWER)
        assert "user@test.com" not in masked
        unmasked = DataMasker.mask_text(text, UserRole.SUPER_ADMIN)
        assert "user@test.com" in unmasked


class TestAuditChain:
    def test_chain_hash_deterministic(self):
        h1 = compute_audit_hash("data1", "prev")
        h2 = compute_audit_hash("data1", "prev")
        assert h1 == h2

    def test_chain_hash_different_data(self):
        h1 = compute_audit_hash("data1", "prev")
        h2 = compute_audit_hash("data2", "prev")
        assert h1 != h2

    def test_chain_integrity(self):
        h1 = compute_audit_hash("event1", "")
        h2 = compute_audit_hash("event2", h1)
        h3 = compute_audit_hash("event3", h2)
        assert len(h3) == 64  # SHA-256


class TestInputSanitization:
    def test_strips_null_bytes(self):
        assert "\x00" not in sanitize_input("hello\x00world")

    def test_truncates_long_input(self):
        result = sanitize_input("a" * 5000, max_length=100)
        assert len(result) == 100

    def test_strips_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"


# ============================================================
# AI Classification Tests
# ============================================================
class TestDataClassifier:
    classifier = DataClassifier()

    def test_detects_email(self):
        result = self.classifier.classify(["user@example.com"])
        assert "EMAIL" in result["detected_entities"]
        assert result["classification"] in ("CONFIDENTIAL", "INTERNAL")

    def test_detects_credit_card(self):
        result = self.classifier.classify(["4111 1111 1111 1111"])
        assert "CREDIT_CARD" in result["detected_entities"]
        assert result["classification"] == "REGULATED"

    def test_detects_saudi_id(self):
        result = self.classifier.classify(["1234567890"])
        assert "SAUDI_NATIONAL_ID" in result["detected_entities"]

    def test_detects_iban(self):
        result = self.classifier.classify(["SA0380000000608010167519"])
        assert "IBAN" in result["detected_entities"]
        assert result["classification"] == "REGULATED"

    def test_arabic_context(self):
        result = self.classifier.classify(
            ["رقم الهوية: 1234567890"],
            language="ar",
        )
        assert len(result["detected_entities"]) > 0
        assert result["confidence_score"] > 0.5

    def test_public_data(self):
        result = self.classifier.classify(["Hello world", "General info"])
        assert result["classification"] == "PUBLIC"
        assert result["confidence_score"] <= 0.6

    def test_sensitive_keywords(self):
        result = self.classifier.classify(["password reset token: abc123"])
        assert result["classification"] == "HIGHLY_SENSITIVE"

    def test_arabic_keywords(self):
        result = self.classifier.classify(["كلمة المرور الخاصة بالحساب"], language="ar")
        assert result["classification"] == "HIGHLY_SENSITIVE"

    def test_explanation_provided(self):
        result = self.classifier.classify(["user@test.com"])
        assert "reasons" in result["explanation"]
        assert len(result["explanation"]["reasons"]) > 0
        assert result["model_version"] is not None


# ============================================================
# Risk Scoring Tests
# ============================================================
class TestRiskEngine:
    engine = RiskScoringEngine()

    def test_low_risk_read(self):
        result = self.engine.evaluate(
            user_id=uuid4(), asset_id=uuid4(), action="READ",
            hour_of_day=10, asset_sensitivity="PUBLIC", user_role="DATA_ANALYST",
        )
        assert result["risk_level"] in ("LOW", "MEDIUM")
        assert result["is_anomaly"] is False

    def test_high_risk_export(self):
        result = self.engine.evaluate(
            user_id=uuid4(), asset_id=uuid4(), action="EXPORT",
            hour_of_day=3, asset_sensitivity="REGULATED",
            user_role="DATA_ANALYST", rows_affected=50000,
        )
        assert result["risk_score"] >= 60
        assert result["risk_level"] in ("HIGH", "CRITICAL")
        assert result["is_anomaly"] is True

    def test_role_mismatch_detection(self):
        result = self.engine.evaluate(
            user_id=uuid4(), asset_id=uuid4(), action="DELETE",
            hour_of_day=14, asset_sensitivity="HIGHLY_SENSITIVE",
            user_role="VIEWER",
        )
        assert any(f["feature"] == "role_action_mismatch" for f in result["factors"])
        assert result["risk_score"] >= 50

    def test_sql_injection_detection(self):
        result = self.engine.evaluate(
            user_id=uuid4(), asset_id=uuid4(), action="READ",
            hour_of_day=10, query_text="SELECT * FROM users WHERE 1=1 -- DROP TABLE users",
        )
        assert any(f["feature"] == "query_pattern" for f in result["factors"])

    def test_factors_provided(self):
        result = self.engine.evaluate(
            user_id=uuid4(), asset_id=uuid4(), action="EXPORT",
            hour_of_day=2, rows_affected=100000,
        )
        assert len(result["factors"]) >= 2
        for factor in result["factors"]:
            assert "feature" in factor
            assert "impact" in factor
            assert "reason" in factor

    def test_recommendation_values(self):
        result = self.engine.evaluate(
            user_id=uuid4(), asset_id=uuid4(), action="READ",
            hour_of_day=12, asset_sensitivity="PUBLIC",
        )
        assert result["recommendation"] in ("ALLOW", "FLAG", "BLOCK")
