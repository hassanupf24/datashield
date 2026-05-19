"""
DATASHIELD Risk Scoring Engine
Anomaly detection and risk assessment with explainable factors.
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.logging_config import get_logger

logger = get_logger(__name__)


class RiskScoringEngine:
    """
    AI-powered risk scoring engine.
    Evaluates access events against behavioral baselines.
    Produces SHAP-style explainable risk factors.
    """

    MODEL_VERSION = "1.0.0-heuristic"

    # Risk thresholds
    THRESHOLDS = {
        "LOW": (0, 30),
        "MEDIUM": (30, 60),
        "HIGH": (60, 85),
        "CRITICAL": (85, 100),
    }

    def evaluate(
        self,
        user_id: UUID,
        asset_id: UUID,
        action: str,
        ip_address: str = "",
        hour_of_day: int | None = None,
        rows_affected: int | None = None,
        asset_sensitivity: str = "UNCLASSIFIED",
        user_role: str = "VIEWER",
        query_text: str | None = None,
    ) -> dict[str, Any]:
        """
        Evaluate the risk of a data access event.

        Returns:
            dict with risk_score, risk_level, is_anomaly, factors, and recommendation.
        """
        if hour_of_day is None:
            hour_of_day = datetime.now(timezone.utc).hour

        factors: list[dict[str, Any]] = []
        total_score = 0.0

        # --- Factor 1: Time of Access ---
        time_score = self._evaluate_time_risk(hour_of_day)
        if time_score > 0:
            factors.append({
                "feature": "access_time",
                "impact": time_score,
                "reason": f"Access at hour {hour_of_day} UTC (outside business hours 7-19)"
                if hour_of_day < 7 or hour_of_day > 19
                else f"Access at hour {hour_of_day} UTC",
            })
        total_score += time_score

        # --- Factor 2: Action Severity ---
        action_score = self._evaluate_action_risk(action)
        factors.append({
            "feature": "action_type",
            "impact": action_score,
            "reason": f"Action '{action}' risk assessment",
        })
        total_score += action_score

        # --- Factor 3: Data Sensitivity ---
        sensitivity_score = self._evaluate_sensitivity_risk(asset_sensitivity)
        if sensitivity_score > 0:
            factors.append({
                "feature": "data_sensitivity",
                "impact": sensitivity_score,
                "reason": f"Accessing {asset_sensitivity} classified data",
            })
        total_score += sensitivity_score

        # --- Factor 4: Volume Analysis ---
        if rows_affected is not None:
            volume_score = self._evaluate_volume_risk(rows_affected)
            if volume_score > 0:
                factors.append({
                    "feature": "data_volume",
                    "impact": volume_score,
                    "reason": f"Query affected {rows_affected} rows",
                })
            total_score += volume_score

        # --- Factor 5: Role-Action Mismatch ---
        mismatch_score = self._evaluate_role_action_mismatch(user_role, action, asset_sensitivity)
        if mismatch_score > 0:
            factors.append({
                "feature": "role_action_mismatch",
                "impact": mismatch_score,
                "reason": f"Role '{user_role}' performing '{action}' on {asset_sensitivity} data",
            })
        total_score += mismatch_score

        # --- Factor 6: Query Pattern Analysis ---
        if query_text:
            query_score = self._evaluate_query_risk(query_text)
            if query_score > 0:
                factors.append({
                    "feature": "query_pattern",
                    "impact": query_score,
                    "reason": "Potentially risky query pattern detected",
                })
            total_score += query_score

        # Normalize score to 0-100
        risk_score = min(round(total_score, 1), 100.0)
        risk_level = self._get_risk_level(risk_score)
        is_anomaly = risk_score >= 70

        recommendation = "ALLOW"
        if risk_score >= 85:
            recommendation = "BLOCK"
        elif risk_score >= 60:
            recommendation = "FLAG"

        if is_anomaly:
            logger.warning(
                "anomaly_detected",
                user_id=str(user_id), asset_id=str(asset_id),
                risk_score=risk_score, risk_level=risk_level,
            )

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "is_anomaly": is_anomaly,
            "factors": factors,
            "recommendation": recommendation,
            "model_version": self.MODEL_VERSION,
        }

    def _evaluate_time_risk(self, hour: int) -> float:
        """Off-hours access increases risk."""
        if hour < 6 or hour > 22:
            return 25.0  # Late night
        if hour < 7 or hour > 19:
            return 10.0  # Early/late
        return 0.0

    def _evaluate_action_risk(self, action: str) -> float:
        """Destructive/export actions carry higher risk."""
        scores = {"READ": 5.0, "WRITE": 15.0, "DELETE": 30.0, "EXPORT": 25.0}
        return scores.get(action.upper(), 10.0)

    def _evaluate_sensitivity_risk(self, sensitivity: str) -> float:
        """Higher sensitivity → higher risk."""
        scores = {
            "PUBLIC": 0.0, "INTERNAL": 5.0, "CONFIDENTIAL": 15.0,
            "HIGHLY_SENSITIVE": 25.0, "REGULATED": 30.0,
        }
        return scores.get(sensitivity, 5.0)

    def _evaluate_volume_risk(self, rows: int) -> float:
        """Large data extractions are suspicious."""
        if rows > 100000:
            return 30.0
        if rows > 10000:
            return 20.0
        if rows > 1000:
            return 10.0
        return 0.0

    def _evaluate_role_action_mismatch(self, role: str, action: str, sensitivity: str) -> float:
        """Detect role-action mismatches (e.g., VIEWER trying EXPORT)."""
        risky_combos = {
            ("VIEWER", "DELETE"): 30.0,
            ("VIEWER", "EXPORT"): 25.0,
            ("DATA_ANALYST", "DELETE"): 20.0,
            ("DATA_ANALYST", "EXPORT"): 10.0,
        }
        score = risky_combos.get((role, action.upper()), 0.0)
        # Extra risk for sensitive data
        if sensitivity in ("HIGHLY_SENSITIVE", "REGULATED") and action.upper() in ("EXPORT", "DELETE"):
            score += 15.0
        return score

    def _evaluate_query_risk(self, query_text: str) -> float:
        """Detect risky SQL patterns."""
        risky_patterns = [
            ("SELECT *", 5.0),
            ("DROP ", 30.0),
            ("DELETE FROM", 20.0),
            ("TRUNCATE", 25.0),
            ("--", 15.0),  # SQL injection indicator
            ("UNION SELECT", 20.0),
            ("INTO OUTFILE", 30.0),
            ("xp_cmdshell", 30.0),
        ]
        score = 0.0
        query_upper = query_text.upper()
        for pattern, risk in risky_patterns:
            if pattern.upper() in query_upper:
                score += risk
        return min(score, 30.0)

    def _get_risk_level(self, score: float) -> str:
        """Map numeric score to risk level."""
        for level, (low, high) in self.THRESHOLDS.items():
            if low <= score < high:
                return level
        return "CRITICAL"


# Singleton instance
risk_engine = RiskScoringEngine()
