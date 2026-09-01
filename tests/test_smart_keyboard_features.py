"""
Unit Test Suite for Phase 1 Smart Keyboard OS Features:
1. Next-Word Ghost Text Prediction
2. Smart Text Expander
3. Local Tone Transformer
4. Enterprise Privacy & PII Guard
"""

import pytest
from engine.autocorrect_service import AutocorrectService
from engine.text_expander import TextExpander
from engine.tone_transformer import ToneTransformer
from engine.privacy_guard import PrivacyGuard


@pytest.fixture(scope="module")
def service():
    return AutocorrectService()


def test_ghost_text_prediction(service):
    preds, lat = service.predict_ghost_text("I want to go to the", top_k=3)
    assert len(preds) > 0
    assert lat < 15.0
    print(f"\n[Test] Ghost Text Prediction for 'I want to go to the': {preds} ({lat:.2f}ms)")


def test_text_expander():
    expander = TextExpander()
    assert expander.is_trigger("//meet") is True
    assert expander.is_trigger("hello") is False

    expansion = expander.expand("//meet")
    assert expansion is not None
    assert "https://calendar.app.google/sync" in expansion

    email_exp = expander.expand("//email")
    assert "@" in email_exp

    today_exp = expander.expand("//today")
    assert len(today_exp) > 5  # Resolved date string


def test_tone_transformer():
    transformer = ToneTransformer()

    # Professional mode
    draft = "hey team, gotta finish this asap. thx"
    prof = transformer.to_professional(draft)
    assert "Hello," in prof
    assert "at your earliest convenience" in prof
    assert "Thank you" in prof

    # Casual mode
    formal = "Please find attached the file at your earliest convenience."
    cas = transformer.to_casual(formal)
    assert "whenever you can" in cas

    # Concise mode
    long_text = "We completed the first phase. Next we will deploy the model. Finally we will test it."
    concise = transformer.to_concise(long_text)
    assert "- We completed" in concise
    assert "- Next we will" in concise


def test_privacy_guard():
    guard = PrivacyGuard()

    # Detect API Key
    text_with_key = "My test OpenAI key is sk-abcdef1234567890abcdef1234567890"
    findings = guard.scan(text_with_key)
    assert len(findings) == 1
    assert findings[0]["hazard"] == "OpenAI / AI Secret Key"

    # Redaction
    redacted = guard.redact(text_with_key)
    assert "sk-" not in redacted
    assert "[REDACTED_OPENAI_/_AI_SECRET_KEY]" in redacted

    # Clean text (no false positive)
    clean_text = "This is a normal email without any confidential data."
    assert len(guard.scan(clean_text)) == 0


def test_compliance_audit_logging(service):
    """Verifies that operations through AutocorrectService generate compliance audit entries."""
    stats_before = service.audit_logger.get_audit_stats()
    count_before = stats_before["total_events"]

    # Trigger a correction
    res = service.evaluate_word("parck", explicit_context="went to the")
    assert res.is_corrected is True

    # Trigger tone transform
    service.transform_tone("hey gotta do it asap", mode="professional")

    # Trigger PII scan & redact
    service.scan_privacy("Token: ghp_1234567890abcdef1234567890abcdef12")
    service.redact_privacy("Token: ghp_1234567890abcdef1234567890abcdef12")

    stats_after = service.audit_logger.get_audit_stats()
    assert stats_after["total_events"] > count_before
    assert stats_after["total_egress_bytes"] == 0
    recent = service.audit_logger.get_recent_events(limit=5)
    assert len(recent) > 0
    assert recent[0]["network_status"] == "AIR_GAPPED"


def test_manual_backspace_override_suppression(service):
    """
    Verifies that when a user backspaces into an autocorrected word and re-types it,
    the word is NOT autocorrected again on the second commit.
    """
    service.reset()
    for w in "I went to the".split():
        for c in w:
            service.feed_character(c)
        service.handle_delimiter_commit(" ")

    # 1. First commit -> corrected
    for c in "parck":
        service.feed_character(c)
    committed, res1 = service.handle_delimiter_commit(" ")
    assert res1.is_corrected is True
    assert res1.corrected_word == "park"

    # 2. User backspaces the delimiter and part of the word
    service.feed_backspace()  # Space
    service.feed_backspace()  # 'k'
    service.feed_backspace()  # 'r'
    service.feed_backspace()  # 'a'

    # 3. User re-types 'arck'
    for c in "arck":
        service.feed_character(c)

    # 4. Second commit -> preserved, no second correction
    committed2, res2 = service.handle_delimiter_commit(" ")
    assert res2.is_corrected is False
    assert res2.corrected_word == "parck"


