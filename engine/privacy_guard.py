"""
Enterprise Privacy Guard & Real-Time PII / Secret Redactor.
Scans text locally for API keys, credit cards, SSNs, and credentials before submission.
"""

import re
from typing import List, Dict, Any


class PrivacyGuard:
    """
    On-device compliance scanner for regulated enterprise environments (HIPAA, SOC2, PCI-DSS).
    Detects API tokens, credentials, SSNs, and credit cards locally.
    """

    def __init__(self):
        self.rules = [
            ("OpenAI / AI Secret Key", r"\bsk-[a-zA-Z0-9_-]{20,}\b"),
            ("GitHub Personal Access Token", r"\bghp_[a-zA-Z0-9]{36}\b"),
            ("AWS Access Key ID", r"\bAKIA[0-9A-Z]{16}\b"),
            ("Social Security Number (SSN)", r"\b\d{3}-\d{2}-\d{4}\b"),
            ("Database Connection String", r"\b(?:postgres|mysql|mongodb(?:\+srv)?):\/\/[^\s]+\b"),
            ("Private Password Assignment", r"\b(?:password|passwd|secret)\s*[:=]\s*['\"][^'\"]+['\"]\b"),
            ("Credit Card Number", r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b"),
        ]

    def scan(self, text: str) -> List[Dict[str, Any]]:
        """
        Scans text and returns a list of detected privacy hazards.
        """
        if not text:
            return []

        findings = []
        for hazard_name, pattern in self.rules:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                val = match.group(0)
                # Mask value preview: show first 3 and last 2 chars
                masked = val[:3] + "*" * (len(val) - 5) + val[-2:] if len(val) > 6 else "****"
                findings.append({
                    "hazard": hazard_name,
                    "matched_text": masked,
                    "start": match.start(),
                    "end": match.end(),
                })

        return findings

    def redact(self, text: str) -> str:
        """
        Replaces all detected sensitive tokens with placeholder redactions.
        """
        if not text:
            return ""

        result = text
        for hazard_name, pattern in self.rules:
            tag = f"[REDACTED_{hazard_name.upper().replace(' ', '_')}]"
            result = re.sub(pattern, tag, result, flags=re.IGNORECASE)

        return result
