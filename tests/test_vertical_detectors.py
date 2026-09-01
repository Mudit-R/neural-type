"""
Unit Test Suite for Vertical-Specific PII Detectors (Healthcare, Legal, Financial).
Uses realistic, synthetic data to verify high-precision pattern matching,
modular activation, and performance isolation.
"""

import pytest
from engine.privacy_guard import (
    PrivacyGuard,
    GenericCredentialsDetector,
    HealthcareDetector,
    LegalDetector,
    FinancialDetector,
)


# ==============================================================================
# 1. Healthcare Vertical Tests (HIPAA / Protected Health Information)
# ==============================================================================
def test_healthcare_detector_mrn_and_patient_id():
    detector = HealthcareDetector()

    # Synthetic MRNs and Patient IDs
    text = "Patient was admitted under MRN-489201 with primary PID: PAT849204."
    findings = detector.scan(text)
    hazards = [f["hazard"] for f in findings]

    assert "Medical Record Number (MRN)" in hazards
    assert "Patient Identifier" in hazards

    # Redaction verification
    redacted = detector.redact(text)
    assert "MRN-489201" not in redacted
    assert "PAT849204" not in redacted
    assert "[REDACTED_MEDICAL_RECORD_NUMBER_(MRN)]" in redacted


def test_healthcare_detector_icd10_codes():
    detector = HealthcareDetector()

    # Synthetic ICD-10 diagnosis codes
    clinical_note = "Assessment: Patient presents with E11.9 (Type 2 diabetes) and acute J45.909 (Asthma)."
    findings = detector.scan(clinical_note)
    icd10_findings = [f for f in findings if f["hazard"] == "ICD-10 Diagnosis Code"]

    assert len(icd10_findings) >= 2

    redacted = detector.redact(clinical_note)
    assert "E11.9" not in redacted
    assert "J45.909" not in redacted


# ==============================================================================
# 2. Legal Vertical Tests (Work-Product & Privilege Protection)
# ==============================================================================
def test_legal_detector_case_dockets():
    detector = LegalDetector()

    # Synthetic Federal & State court case docket numbers
    pleading = "In the Matter of 1:23-cv-04567 pending before SDNY, also ref Case No. 2024-CA-001245."
    findings = detector.scan(pleading)
    dockets = [f for f in findings if f["hazard"] == "Court Docket Number"]

    assert len(dockets) >= 2

    redacted = detector.redact(pleading)
    assert "1:23-cv-04567" not in redacted
    assert "2024-CA-001245" not in redacted


def test_legal_detector_privileged_phrases():
    detector = LegalDetector()

    # Synthetic attorney-client privileged memos
    memo = "ATTORNEY-CLIENT PRIVILEGED & CONFIDENTIAL: Prepared in Anticipation of Litigation."
    findings = detector.scan(memo)
    priv_findings = [f for f in findings if f["hazard"] == "Privileged Communication Flag"]

    assert len(priv_findings) >= 1

    redacted = detector.redact(memo)
    assert "[REDACTED_PRIVILEGED_COMMUNICATION_FLAG]" in redacted


# ==============================================================================
# 3. Financial Vertical Tests (GLBA & PCI-DSS Protection)
# ==============================================================================
def test_financial_detector_routing_and_accounts():
    detector = FinancialDetector()

    # Synthetic Bank Routing and Account Numbers
    wire_instruction = "Wire details: Routing: 021000021, Account: 987654321098."
    findings = detector.scan(wire_instruction)
    hazards = [f["hazard"] for f in findings]

    assert "Bank Routing Transit Number (ABA)" in hazards
    assert "Bank Account Number" in hazards

    redacted = detector.redact(wire_instruction)
    assert "021000021" not in redacted
    assert "987654321098" not in redacted


def test_financial_detector_swift_and_iban():
    detector = FinancialDetector()

    # Synthetic SWIFT / BIC and IBAN numbers
    cross_border = "Intermediary Bank: CHASUS33, Beneficiary IBAN: GB29NWBK60161331926819."
    findings = detector.scan(cross_border)
    hazards = [f["hazard"] for f in findings]

    assert "SWIFT / BIC Code" in hazards
    assert "IBAN Number" in hazards

    redacted = detector.redact(cross_border)
    assert "CHASUS33" not in redacted
    assert "GB29NWBK60161331926819" not in redacted


# ==============================================================================
# 4. Modular Profile Isolation Tests
# ==============================================================================
def test_privacy_guard_profile_isolation():
    """
    Verifies that choosing a specific vertical profile skips overhead and
    detection of other vertical patterns.
    """
    # 1. Legal-only profile
    legal_guard = PrivacyGuard(vertical_profile="legal")
    healthcare_text = "Clinical note: Patient MRN-123456 diagnosed with E11.9."
    # Should NOT detect healthcare data when in legal profile
    assert len(legal_guard.scan(healthcare_text)) == 0

    legal_text = "Re: Case 1:23-cv-09876 - ATTORNEY-CLIENT PRIVILEGED memo."
    legal_findings = legal_guard.scan(legal_text)
    assert len(legal_findings) >= 2

    # 2. Healthcare-only profile
    health_guard = PrivacyGuard(vertical_profile="healthcare")
    financial_text = "Wire to IBAN: DE89370400440532013000, SWIFT: DEUTDEFF500."
    # Should NOT detect financial data when in healthcare profile
    assert len(health_guard.scan(financial_text)) == 0

    health_findings = health_guard.scan(healthcare_text)
    assert len(health_findings) >= 2

    # 3. All profile
    all_guard = PrivacyGuard(vertical_profile="all")
    mixed_text = "Case 1:23-cv-09876 with MRN-123456 and IBAN GB29NWBK60161331926819."
    all_findings = all_guard.scan(mixed_text)
    assert len(all_findings) >= 3


def test_fine_grained_rule_toggling():
    """Verifies that individual detector rules can be disabled while keeping the module active."""
    # Disable specifically icd10 diagnosis codes
    guard = PrivacyGuard(
        vertical_profile="healthcare",
        detector_rules={"icd10_diagnosis_codes": False, "medical_record_numbers": True},
    )

    text = "Patient MRN-489201 evaluated for diagnosis E11.9."
    findings = guard.scan(text)
    hazards = [f["hazard"] for f in findings]

    assert "Medical Record Number (MRN)" in hazards
    assert "ICD-10 Diagnosis Code" not in hazards
