"""
DATASHIELD AI Classification Engine
Rule-based + ML-powered data sensitivity classification with Arabic NLP support.
"""
from __future__ import annotations

import re
from typing import Any

from app.logging_config import get_logger

logger = get_logger(__name__)

# Sensitivity levels
SENSITIVITY_LEVELS = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "HIGHLY_SENSITIVE", "REGULATED"]


# --- PII Detection Patterns (English + Arabic) ---
PII_PATTERNS = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE_INTL": re.compile(r"\+?\d{1,4}[\s-]?\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4}"),
    "CREDIT_CARD": re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]{0,16})\b"),
    "SAUDI_NATIONAL_ID": re.compile(r"\b[12]\d{9}\b"),
    "UAE_EMIRATES_ID": re.compile(r"\b784-?\d{4}-?\d{7}-?\d\b"),
    "PASSPORT": re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),
    "IP_ADDRESS": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "SSN_US": re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
}

# Arabic-specific PII patterns
ARABIC_PII_PATTERNS = {
    "ARABIC_NAME": re.compile(r"[\u0600-\u06FF\s]{3,50}"),  # Arabic text segments
    "ARABIC_NATIONAL_ID_CONTEXT": re.compile(
        r"(?:رقم الهوية|الهوية الوطنية|رقم الجواز|الرقم الوطني)[\s:]*\d+"
    ),
    "ARABIC_PHONE_CONTEXT": re.compile(
        r"(?:رقم الهاتف|الجوال|الموبايل|هاتف)[\s:]*[\d\s+-]+"
    ),
    "ARABIC_EMAIL_CONTEXT": re.compile(
        r"(?:البريد الإلكتروني|الإيميل|بريد)[\s:]*\S+@\S+"
    ),
    "ARABIC_ADDRESS": re.compile(
        r"(?:العنوان|الحي|الشارع|المدينة|المنطقة)[\s:]*[\u0600-\u06FF\s\d,]+"
    ),
}

# Financial data patterns
FINANCIAL_PATTERNS = {
    "CURRENCY_AMOUNT": re.compile(r"(?:SAR|AED|USD|EUR|GBP|ر\.س|د\.إ)\s*[\d,]+\.?\d*"),
    "ACCOUNT_NUMBER": re.compile(r"\b\d{10,16}\b"),
    "SWIFT_CODE": re.compile(r"\b[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?\b"),
}

# Sensitive keyword lists
SENSITIVE_KEYWORDS_EN = {
    "HIGHLY_SENSITIVE": ["password", "secret", "ssn", "social security", "credit card",
                          "cvv", "pin", "private key", "encryption key"],
    "CONFIDENTIAL": ["salary", "medical", "health", "diagnosis", "patient",
                      "criminal", "arrest", "conviction"],
    "REGULATED": ["pci", "hipaa", "gdpr", "pdpl", "cardholder"],
}

SENSITIVE_KEYWORDS_AR = {
    "HIGHLY_SENSITIVE": ["كلمة المرور", "سري", "الرقم السري", "بطاقة الائتمان",
                          "المفتاح الخاص"],
    "CONFIDENTIAL": ["الراتب", "طبي", "صحي", "تشخيص", "مريض", "جنائي"],
    "REGULATED": ["بيانات شخصية", "حماية البيانات", "بطاقة دفع"],
}


class DataClassifier:
    """
    AI-powered data sensitivity classifier.
    Uses a hybrid approach: regex patterns + keyword matching + statistical analysis.
    Produces explainable results (XAI-ready).
    """

    MODEL_VERSION = "1.0.0-rule-based"

    def classify(
        self,
        sample_data: list[str],
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Classify a batch of data samples and return sensitivity level with explanation.

        Returns:
            dict with classification, confidence, detected_entities, and explanation.
        """
        detected_entities: list[dict[str, Any]] = []
        entity_types: set[str] = set()
        max_sensitivity = "PUBLIC"
        explanations: list[str] = []

        for sample in sample_data:
            if not sample or not isinstance(sample, str):
                continue

            # PII pattern matching
            for entity_type, pattern in PII_PATTERNS.items():
                matches = pattern.findall(sample)
                if matches:
                    entity_types.add(entity_type)
                    detected_entities.append({
                        "type": entity_type,
                        "count": len(matches),
                        "sample_match": self._mask_match(matches[0]),
                    })
                    explanations.append(f"Detected {entity_type} pattern ({len(matches)} match(es))")

            # Arabic PII patterns
            if language == "ar" or self._contains_arabic(sample):
                for entity_type, pattern in ARABIC_PII_PATTERNS.items():
                    matches = pattern.findall(sample)
                    if matches:
                        entity_types.add(entity_type)
                        detected_entities.append({
                            "type": entity_type,
                            "count": len(matches),
                        })
                        explanations.append(f"كشف نمط {entity_type} ({len(matches)} تطابق)")

            # Financial patterns
            for entity_type, pattern in FINANCIAL_PATTERNS.items():
                matches = pattern.findall(sample)
                if matches:
                    entity_types.add(entity_type)
                    detected_entities.append({
                        "type": entity_type,
                        "count": len(matches),
                    })

            # Keyword matching
            keywords = SENSITIVE_KEYWORDS_AR if language == "ar" else SENSITIVE_KEYWORDS_EN
            for level, kw_list in keywords.items():
                sample_lower = sample.lower()
                for kw in kw_list:
                    if kw.lower() in sample_lower:
                        entity_types.add(f"KEYWORD_{level}")
                        explanations.append(f"Sensitive keyword detected: '{kw}' → {level}")

        # Determine sensitivity level
        max_sensitivity = self._compute_sensitivity(entity_types)
        confidence = self._compute_confidence(entity_types, len(sample_data))

        return {
            "classification": max_sensitivity,
            "confidence_score": confidence,
            "detected_entities": list(entity_types),
            "explanation": {
                "model_version": self.MODEL_VERSION,
                "reasons": explanations,
                "entity_details": detected_entities,
            },
            "model_version": self.MODEL_VERSION,
        }

    def _compute_sensitivity(self, entity_types: set[str]) -> str:
        """Determine the highest applicable sensitivity level."""
        if any("HIGHLY_SENSITIVE" in e for e in entity_types):
            return "HIGHLY_SENSITIVE"
        if any(e in entity_types for e in ["CREDIT_CARD", "SSN_US", "SAUDI_NATIONAL_ID", "UAE_EMIRATES_ID"]):
            return "REGULATED"
        if any(e in entity_types for e in ["IBAN", "SWIFT_CODE", "CURRENCY_AMOUNT", "KEYWORD_REGULATED"]):
            return "REGULATED"
        if any(e in entity_types for e in ["EMAIL", "PHONE_INTL", "PASSPORT", "KEYWORD_CONFIDENTIAL"]):
            return "CONFIDENTIAL"
        if any(e in entity_types for e in ["ARABIC_NAME", "ARABIC_ADDRESS", "IP_ADDRESS"]):
            return "INTERNAL"
        if entity_types:
            return "INTERNAL"
        return "PUBLIC"

    def _compute_confidence(self, entity_types: set[str], sample_count: int) -> float:
        """Compute confidence score based on evidence strength."""
        if not entity_types:
            return 0.5
        base = min(0.6 + len(entity_types) * 0.1, 0.99)
        # Higher confidence with more samples
        sample_boost = min(sample_count / 10, 1.0) * 0.1
        return round(min(base + sample_boost, 0.99), 2)

    def _contains_arabic(self, text: str) -> bool:
        """Check if text contains Arabic characters."""
        return bool(re.search(r"[\u0600-\u06FF]", text))

    def _mask_match(self, match: str) -> str:
        """Mask a matched PII value for safe logging."""
        if len(match) <= 4:
            return "***"
        return match[:2] + "*" * (len(match) - 4) + match[-2:]


# Singleton instance
classifier = DataClassifier()
