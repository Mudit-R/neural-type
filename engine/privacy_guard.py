"""
Enterprise Privacy Guard & Vertical Compliance Scanner.
Detects credentials, API keys, and vertical-specific sensitive data:
- Generic: API keys, tokens, SSNs, credit cards, DB URIs, passwords.
- Healthcare: MRNs, patient IDs, ICD-10 diagnosis codes (HIPAA).
- Legal: Case docket numbers, attorney-client privileged banners.
- Financial: Routing numbers, account numbers, SWIFT/BIC, IBANs (GLBA/PCI-DSS).

All detector modules are independently toggleable to eliminate overhead for inactive verticals.
"""

import re
from typing import List, Dict, Any, Optional, Tuple


class BaseDetectorModule:
    """Base class for compliance detector modules."""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.rules: List[Tuple[str, str, str]] = []  # (rule_id, hazard_name, regex_pattern)

    def scan(self, text: str, active_rules: Optional[Dict[str, bool]] = None) -> List[Dict[str, Any]]:
        """Scans text against enabled regex patterns."""
        if not self.enabled or not text:
            return []

        findings = []
        for rule_id, hazard_name, pattern in self.rules:
            if active_rules is not None and not active_rules.get(rule_id, True):
                continue

            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                val = match.group(0)
                # Mask preview: show prefix & suffix if length > 6
                if len(val) > 6:
                    masked = val[:3] + "*" * (len(val) - 5) + val[-2:]
                else:
                    masked = "****"

                findings.append({
                    "module": self.name,
                    "rule_id": rule_id,
                    "hazard": hazard_name,
                    "matched_text": masked,
                    "start": match.start(),
                    "end": match.end(),
                })
        return findings

    def redact(self, text: str, active_rules: Optional[Dict[str, bool]] = None) -> str:
        """Applies redaction placeholders to matches in text."""
        if not self.enabled or not text:
            return text

        result = text
        for rule_id, hazard_name, pattern in self.rules:
            if active_rules is not None and not active_rules.get(rule_id, True):
                continue
            tag = f"[REDACTED_{hazard_name.upper().replace(' ', '_').replace('-', '_')}]"
            result = re.sub(pattern, tag, result, flags=re.IGNORECASE)
        return result


class GenericCredentialsDetector(BaseDetectorModule):
    """Detects API tokens, credentials, SSNs, and credit cards."""

    def __init__(self, enabled: bool = True):
        super().__init__(name="generic", enabled=enabled)
        self.rules = [
            ("ai_secret_keys", "OpenAI / AI Secret Key", r"\bsk-[a-zA-Z0-9_-]{20,}\b"),
            ("github_tokens", "GitHub Personal Access Token", r"\bghp_[a-zA-Z0-9]{36}\b"),
            ("aws_access_keys", "AWS Access Key ID", r"\bAKIA[0-9A-Z]{16}\b"),
            ("social_security_numbers", "Social Security Number (SSN)", r"\b\d{3}-\d{2}-\d{4}\b"),
            ("database_uris", "Database Connection String", r"\b(?:postgres|mysql|mongodb(?:\+srv)?):\/\/[^\s]+\b"),
            ("credentials_passwords", "Private Password Assignment", r"\b(?:password|passwd|secret)\s*[:=]\s*['\"][^'\"]+['\"]\b"),
            ("credit_cards", "Credit Card Number", r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b"),
        ]


class HealthcareDetector(BaseDetectorModule):
    """Detects HIPAA Protected Health Information (MRNs, Patient IDs, ICD-10 codes)."""

    def __init__(self, enabled: bool = True):
        super().__init__(name="healthcare", enabled=enabled)
        self.rules = [
            ("medical_record_numbers", "Medical Record Number (MRN)", r"\b(?:MRN|MEDREC)[:#\s-]*([A-Z0-9]{6,10})\b|\bMRN-\d{6,8}\b"),
            ("patient_ids", "Patient Identifier", r"\b(?:Patient\s*ID|PID)[:#\s]*([A-Z0-9]{6,12})\b"),
            ("icd10_diagnosis_codes", "ICD-10 Diagnosis Code", r"\b[A-TV-Z][0-9][0-9AB](?:\.[0-9A-KXZ]{1,4})?\b"),
        ]


class LegalDetector(BaseDetectorModule):
    """Detects legal work-product, docket numbers, and attorney-client privilege banners."""

    def __init__(self, enabled: bool = True):
        super().__init__(name="legal", enabled=enabled)
        self.rules = [
            ("case_docket_numbers", "Court Docket Number", r"\b(?:\d{1,2}:)?\d{2}-(?:cv|cr|mc|mj|bk|ap)-\d{4,6}(?:-[A-Z]{2,4})?\b|\bCase\s*(?:No\.|#|Number)[:\s]*\d{4}-[A-Z]{2,4}-\d{4,8}\b"),
            ("privileged_phrases", "Privileged Communication Flag", r"(?i)\b(?:Attorney-Client\s+Privileg(?:ed|e)|Work[- ]Product\s+Doctrine|Confidential\s+Legal\s+Advice|Prepared\s+in\s+Anticipation\s+of\s+Litigation|Privileged\s+and\s+Confidential)\b"),
        ]


class FinancialDetector(BaseDetectorModule):
    """Detects financial account identifiers, routing numbers, SWIFT/BIC, and IBANs."""

    def __init__(self, enabled: bool = True):
        super().__init__(name="financial", enabled=enabled)
        self.rules = [
            ("bank_routing_numbers", "Bank Routing Transit Number (ABA)", r"\b(?:Routing\s*(?:#|Number|No\.?)?[:\s]*|ABA[:\s#]*)([0-3]\d{8})\b"),
            ("bank_account_numbers", "Bank Account Number", r"\b(?:Account\s*(?:#|Number|No\.?)?|ACCT)[:\s#]*([0-9]{8,17})\b"),
            ("swift_bic_codes", "SWIFT / BIC Code", r"\b[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b"),
            ("iban_numbers", "IBAN Number", r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
        ]


class PrivacyGuard:
    """
    On-device modular compliance scanner for regulated enterprise environments.
    Orchestrates generic and vertical-specific detector modules according to policy.
    """

    def __init__(
        self,
        enabled: bool = True,
        vertical_profile: str = "all",
        detector_rules: Optional[Dict[str, bool]] = None,
    ):
        self.enabled = enabled
        self.vertical_profile = vertical_profile.lower()
        self.detector_rules = detector_rules or {}

        # Initialize detector modules
        self.generic_module = GenericCredentialsDetector()
        self.healthcare_module = HealthcareDetector()
        self.legal_module = LegalDetector()
        self.financial_module = FinancialDetector()

        self._configure_active_modules()

    def _configure_active_modules(self) -> None:
        """Enables/disables modules based on vertical_profile."""
        if not self.enabled:
            self.generic_module.enabled = False
            self.healthcare_module.enabled = False
            self.legal_module.enabled = False
            self.financial_module.enabled = False
            return

        if self.vertical_profile == "all":
            self.generic_module.enabled = True
            self.healthcare_module.enabled = True
            self.legal_module.enabled = True
            self.financial_module.enabled = True
        elif self.vertical_profile == "healthcare":
            self.generic_module.enabled = True
            self.healthcare_module.enabled = True
            self.legal_module.enabled = False
            self.financial_module.enabled = False
        elif self.vertical_profile == "legal":
            self.generic_module.enabled = True
            self.healthcare_module.enabled = False
            self.legal_module.enabled = True
            self.financial_module.enabled = False
        elif self.vertical_profile == "financial":
            self.generic_module.enabled = True
            self.healthcare_module.enabled = False
            self.legal_module.enabled = False
            self.financial_module.enabled = True
        elif self.vertical_profile == "general":
            self.generic_module.enabled = True
            self.healthcare_module.enabled = False
            self.legal_module.enabled = False
            self.financial_module.enabled = False
        else:
            self.generic_module.enabled = True

    def set_vertical_profile(self, profile: str) -> None:
        """Switches active vertical profile at runtime."""
        self.vertical_profile = profile.lower()
        self._configure_active_modules()

    def scan(self, text: str) -> List[Dict[str, Any]]:
        """Scans text across all active detector modules."""
        if not self.enabled or not text:
            return []

        findings = []
        modules = [
            self.generic_module,
            self.healthcare_module,
            self.legal_module,
            self.financial_module,
        ]

        for mod in modules:
            if mod.enabled:
                findings.extend(mod.scan(text, active_rules=self.detector_rules))

        return findings

    def redact(self, text: str) -> str:
        """Applies placeholder redactions for all active detector modules."""
        if not self.enabled or not text:
            return text

        result = text
        modules = [
            self.generic_module,
            self.healthcare_module,
            self.legal_module,
            self.financial_module,
        ]

        for mod in modules:
            if mod.enabled:
                result = mod.redact(result, active_rules=self.detector_rules)

        return result
