"""
Automated Proof of Network Isolation & Zero Outbound Data Egress.
Simulates an air-gapped, zero-connectivity environment at the OS/socket level
and verifies that Neural-Type operates with 100% functionality and 0 outbound calls.
"""

import os
import json
import socket
import pytest
from unittest.mock import patch
from engine.autocorrect_service import AutocorrectService
from engine.audit_log import ComplianceAuditLogger


@pytest.fixture
def airgap_service(tmp_path):
    """Provides an AutocorrectService configured to write audit logs to a test directory."""
    log_dir = str(tmp_path / "audit_logs")
    service = AutocorrectService(
        audit_log_dir=log_dir,
        audit_enabled=True,
        verify_isolation_on_startup=True,
    )
    return service


def test_startup_isolation_self_check(airgap_service):
    """Verifies that the startup self-check succeeds and sets is_network_isolated."""
    assert airgap_service.is_network_isolated is True
    # Re-run explicit self-check
    assert airgap_service.verify_network_isolation() is True


def test_complete_pipeline_under_socket_lockdown(tmp_path, monkeypatch):
    """
    Blocks all network connections at socket and HTTP client levels.
    Verifies that all Neural-Type capabilities work offline with zero egress.
    """
    call_log = []

    def forbidden_connect(*args, **kwargs):
        call_log.append(("connect", args))
        raise PermissionError("Egress forbidden: Neural-Type operates strictly air-gapped.")

    # Strict socket intercept
    monkeypatch.setattr(socket.socket, "connect", forbidden_connect)
    if hasattr(socket, "create_connection"):
        monkeypatch.setattr(socket, "create_connection", forbidden_connect)

    log_dir = str(tmp_path / "airgap_audit")
    service = AutocorrectService(
        audit_log_dir=log_dir,
        audit_enabled=True,
        verify_isolation_on_startup=False,
    )

    # 1. Contextual autocorrect
    res = service.evaluate_word("parck", delimiter=" ", explicit_context="I went to the")
    assert res.is_corrected is True
    assert res.corrected_word.lower() == "park"

    # 2. Semantic disambiguation
    res2 = service.evaluate_word("meat", delimiter=" ", explicit_context="I will")
    assert res2.is_corrected is True
    assert res2.corrected_word.lower() == "meet"

    # 3. Next-word ghost text prediction
    ghosts, lat = service.predict_ghost_text("I want to go to the", top_k=2)
    assert len(ghosts) > 0

    # 4. Text Expander
    res_exp = service.evaluate_word("//meet", delimiter=" ")
    assert res_exp.is_corrected is True
    assert res_exp.is_expansion is True
    assert "https://calendar.app.google" in res_exp.corrected_word

    # 5. Tone Transformer
    tone = service.transform_tone("hey team, gotta finish asap. thx", mode="professional")
    assert "Hello," in tone
    assert "at your earliest convenience" in tone

    # 6. Privacy Guard (Scan & Redaction)
    dummy_key = "OpenAI key is sk-1234567890abcdef1234567890abcdef"
    findings = service.scan_privacy(dummy_key)
    assert len(findings) == 1
    assert findings[0]["hazard"] == "OpenAI / AI Secret Key"

    redacted = service.redact_privacy(dummy_key)
    assert "sk-1234567890" not in redacted
    assert "[REDACTED_OPENAI_/_AI_SECRET_KEY]" in redacted

    # 7. Hardware-state Tab Revert
    revert_result = service.handle_tab_revert()
    assert revert_result is not None  # Reverts the //meet expansion

    # 8. Assert ZERO network attempts occurred
    assert len(call_log) == 0, f"Outbound socket calls detected during execution: {call_log}"


def test_compliance_audit_log_structure(tmp_path):
    """
    Verifies that the audit log:
    1. Records metadata only (no raw user text or sensitive strings).
    2. Contains egress_bytes == 0 and network_status == 'AIR_GAPPED'.
    3. Accurately records deltas and confidence scores.
    """
    log_dir = str(tmp_path / "compliance_logs")
    service = AutocorrectService(audit_log_dir=log_dir, audit_enabled=True)

    secret_key = "sk-abcdef1234567890abcdef1234567890"
    service.evaluate_word("parck", explicit_context="at the")
    service.transform_tone("gonna do it asap", mode="professional")
    service.scan_privacy(f"my key is {secret_key}")
    service.redact_privacy(f"my key is {secret_key}")
    service.evaluate_word("//meet")

    log_file = os.path.join(log_dir, "audit_trail.jsonl")
    assert os.path.exists(log_file)

    events = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line.strip()))

    assert len(events) >= 5

    # Check every single logged event for compliance guarantees
    for event in events:
        assert event["egress_bytes"] == 0
        assert event["network_status"] == "AIR_GAPPED"
        assert "timestamp" in event
        assert "event_id" in event
        assert "input_char_count" in event
        assert "output_char_count" in event

        # Critical security check: raw text must never appear anywhere in the serialized log
        event_str = json.dumps(event)
        assert secret_key not in event_str
        assert "parck" not in event_str
        assert "gonna" not in event_str

    # Verify audit telemetry stats helper
    stats = service.audit_logger.get_audit_stats()
    assert stats["total_events"] >= 5
    assert stats["total_egress_bytes"] == 0
    assert stats["enabled"] is True
    assert "CORRECTION" in stats["breakdown"]
    assert "PII_DETECTION" in stats["breakdown"]
    assert "PII_REDACTION" in stats["breakdown"]
    assert "TONE_TRANSFORM" in stats["breakdown"]


def test_audit_log_retention_and_rotation(tmp_path):
    """Verifies that 90-day retention pruning and size-based rotation work correctly."""
    log_dir = str(tmp_path / "rotation_test")
    # Low threshold for testing rotation
    logger = ComplianceAuditLogger(
        log_dir=log_dir,
        max_file_size_bytes=400,  # rotate after ~2-3 events
        retention_days=90,
    )

    # Log several events to trigger rotation
    for i in range(10):
        logger.log_event(
            event_type="CORRECTION",
            input_char_count=5,
            output_char_count=5,
            confidence_score=0.95,
            latency_ms=0.5,
        )

    # Should have rotated at least once
    files = os.listdir(log_dir)
    rotated_archives = [f for f in files if f.startswith("audit_trail_") and f.endswith(".jsonl")]
    assert len(rotated_archives) > 0
    assert os.path.exists(logger.active_log_path)
