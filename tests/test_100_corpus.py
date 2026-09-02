"""
100-Test Comprehensive Benchmark & Verification Suite for NeuraType AI Keyboard.
Tests:
- 25 Common Misspellings & Typo Transpositions
- 20 Homophones & Real-Word Confusable Disambiguations
- 15 Contractions without Apostrophes
- 10 Code, URL, and Syntax Guards
- 10 Proper Noun & Named Entity Preservations
- 5 Snippet Expander Triggers
- 5 Enterprise Privacy Guard Scans & Redactions
- 5 Local Tone Transformations
- 5 Tab Reverts & Manual Backspace Override Tests
- 10 20-Word Context Sentences & Long-Range Repetitions
Total: 100 Independent Tests
"""

import pytest
from engine.autocorrect_service import AutocorrectService
from engine.text_expander import TextExpander
from engine.tone_transformer import ToneTransformer
from engine.privacy_guard import PrivacyGuard


@pytest.fixture(scope="module")
def service():
    return AutocorrectService(confidence_threshold=0.60, revert_timeout=3.5)


# ==============================================================================
# SECTION 1: 25 Common Misspellings & Typo Transpositions
# ==============================================================================
TYPO_CASES = [
    ("I went to the", "parck", "park"),
    ("He walked into the", "feild", "field"),
    ("I will", "definately", "definitely"),
    ("She did not", "recieve", "receive"),
    ("That was very", "wierd", "weird"),
    ("Please check the", "calender", "calendar"),
    ("It is absolutely", "neccessary", "necessary"),
    ("The incident", "occured", "occurred"),
    ("See you", "tomorow", "tomorrow"),
    ("See you", "tommorrow", "tomorrow"),
    ("Wait here", "untill", "until"),
    ("Keep them", "seperate", "separate"),
    ("Federal", "goverment", "government"),
    ("I cannot", "belive", "believe"),
    ("You can", "acheive", "achieve"),
    ("Spelled in a", "fonetic", "phonetic"),
    ("I am", "truely", "truly"),
    ("I am", "nowt", "not"),
    ("They", "hvae", "have"),
    ("I", "woudl", "would"),
    ("You", "shoudl", "should"),
    ("Done", "becuase", "because"),
    ("This is", "teh", "the"),
    ("Look at", "thier", "their"),
    ("Measure the", "lenght", "length"),
]


@pytest.mark.parametrize("ctx, typo, expected", TYPO_CASES)
def test_common_typos(service, ctx, typo, expected):
    res = service.evaluate_word(typo, explicit_context=ctx)
    assert res.is_corrected is True, f"Failed for typo '{typo}' in context '{ctx}'"
    assert res.corrected_word.lower() == expected.lower()


# ==============================================================================
# SECTION 2: 20 Homophones & Real-Word Confusable Disambiguations
# ==============================================================================
HOMOPHONE_CASES = [
    ("We should schedule a time to", "meat", "meet"),
    ("I would love to have some grilled", "meet", "meat"),
    ("I bought a brand new", "pare", "pair"),
    ("We need world", "peace", "peace"),
    ("Have a delicious", "piece", "piece"),
    ("They are over", "there", "there"),       # Preserve correct
    ("Check out", "their", "their"),           # Preserve correct
    ("Going", "to", "to"),                     # Preserve correct
    ("It is way too", "far", "far"),
    ("Take", "your", "your"),                  # Preserve correct
    ("I know that", "you're", "you're"),
    ("The cat licked", "its", "its"),          # Preserve correct
    ("Check the forecast", "weather", "weather"), # Preserve correct
    ("I wonder", "whether", "whether"),
    ("I cannot", "hear", "hear"),              # Preserve correct
    ("Come over", "here", "here"),
    ("I want to", "buy", "buy"),               # Preserve correct
    ("Standing right", "by", "by"),
    ("Sail across the deep blue", "sea", "sea"),
    ("Step on the emergency car", "brake", "brake"),
]


@pytest.mark.parametrize("ctx, word, expected", HOMOPHONE_CASES)
def test_homophone_disambiguation(service, ctx, word, expected):
    res = service.evaluate_word(word, explicit_context=ctx)
    if word == expected:
        assert res.corrected_word.lower() == expected.lower()
    else:
        assert res.is_corrected is True
        assert res.corrected_word.lower() == expected.lower()


# ==============================================================================
# SECTION 3: 15 Contractions Without Apostrophes
# ==============================================================================
CONTRACTION_CASES = [
    ("dont", "don't"),
    ("cant", "can't"),
    ("wont", "won't"),
    ("didnt", "didn't"),
    ("isnt", "isn't"),
    ("arent", "aren't"),
    ("wasnt", "wasn't"),
    ("werent", "weren't"),
    ("hasnt", "hasn't"),
    ("havent", "haven't"),
    ("hadnt", "hadn't"),
    ("doesnt", "doesn't"),
    ("couldnt", "couldn't"),
    ("shouldnt", "shouldn't"),
    ("theyre", "they're"),
]


@pytest.mark.parametrize("raw, expected", CONTRACTION_CASES)
def test_contractions(service, raw, expected):
    res = service.evaluate_word(raw, explicit_context="I")
    assert res.is_corrected is True
    assert res.corrected_word == expected


# ==============================================================================
# SECTION 4: 10 Code, URL, and Syntax Guards
# ==============================================================================
SYNTAX_GUARD_CASES = [
    ("https://github.com/neural-type"),
    ("http://localhost:8000/api"),
    ("user_id"),
    ("get_user_account_by_id"),
    ("Python3"),
    ("v1.2.3"),
    ("0x7FFE2B"),
    ("C:\\ProgramData\\NeuraType"),
    ("/usr/local/bin"),
    ("user@domain.com"),
]


@pytest.mark.parametrize("code_token", SYNTAX_GUARD_CASES)
def test_syntax_guards(service, code_token):
    res = service.evaluate_word(code_token, explicit_context="variable")
    assert res.is_corrected is False
    assert res.corrected_word == code_token


# ==============================================================================
# SECTION 5: 10 Proper Noun & Named Entity Preservations
# ==============================================================================
PROPER_NOUN_CASES = [
    ("Mohit"),
    ("Google"),
    ("BillDesk"),
    ("Microsoft"),
    ("London"),
    ("PyTorch"),
    ("iPhone"),
    ("Razorpay"),
    ("Tesla"),
    ("NVIDIA"),
]


@pytest.mark.parametrize("name", PROPER_NOUN_CASES)
def test_proper_nouns(service, name):
    res = service.evaluate_word(name, explicit_context="I met with")
    assert res.is_corrected is False
    assert res.corrected_word == name


# ==============================================================================
# SECTION 6: 5 Snippet Expander Triggers
# ==============================================================================
EXPANDER_CASES = [
    ("//meet", "https://calendar.app.google/sync"),
    ("//email", "@"),
    ("//today", "202"),
    ("//zoom", "https://zoom.us/j/"),
    ("//sig", "Best regards"),
]


@pytest.mark.parametrize("trigger, expected_content", EXPANDER_CASES)
def test_expander_snippets(service, trigger, expected_content):
    expander = TextExpander()
    assert expander.is_trigger(trigger) is True
    val = expander.expand(trigger)
    assert val is not None
    assert expected_content in val


# ==============================================================================
# SECTION 7: 5 Enterprise Privacy Guard Scans & Redactions
# ==============================================================================
PRIVACY_CASES = [
    ("sk-1234567890abcdefghijklmnopqrstuvwxyz", "AI Secret Key"),
    ("AKIAIOSFODNN7EXAMPLE", "AWS Access Key"),
    ("My ssn is 123-45-6789 confidential", "SSN"),
    ("Card 4532123456789012 valid", "Credit Card"),
    ("ghp_123456789012345678901234567890123456", "GitHub Token"),
]


@pytest.mark.parametrize("text, hazard_type", PRIVACY_CASES)
def test_privacy_guard_scan_and_redact(text, hazard_type):
    guard = PrivacyGuard(enabled=True)
    findings = guard.scan(text)
    assert len(findings) > 0
    redacted = guard.redact(text)
    assert "[REDACTED" in redacted


# ==============================================================================
# SECTION 8: 5 Local Tone Transformations
# ==============================================================================
def test_tone_professional_mode():
    transformer = ToneTransformer()
    res = transformer.to_professional("hey team, gotta wrap this asap. thx")
    assert "Hello," in res
    assert "Thank you" in res


def test_tone_casual_mode():
    transformer = ToneTransformer()
    res = transformer.to_casual("Please find attached the report at your earliest convenience.")
    assert "whenever you can" in res


def test_tone_concise_mode():
    transformer = ToneTransformer()
    res = transformer.to_concise("We finished the first phase. Next we deploy. Finally we test.")
    assert "- We finished" in res


def test_tone_empty_string():
    transformer = ToneTransformer()
    assert transformer.to_professional("") == ""


def test_tone_already_clean():
    transformer = ToneTransformer()
    res = transformer.to_professional("Good morning team.")
    assert len(res) > 0


# ==============================================================================
# SECTION 9: 5 Tab Reverts & Manual Backspace Override Tests
# ==============================================================================
def test_tab_revert_flow(service):
    service.reset()
    service.feed_character("p")
    service.feed_character("a")
    service.feed_character("r")
    service.feed_character("c")
    service.feed_character("k")
    _, res = service.handle_delimiter_commit(" ")
    assert res.is_corrected is True
    assert res.corrected_word == "park"

    # Tab restores original
    revert = service.handle_tab_revert()
    assert revert is not None
    corrected, original, delim = revert
    assert corrected == "park"
    assert original == "parck"


def test_tab_revert_disarmed_on_character(service):
    service.reset()
    service.undo_manager.record_correction("typo", "type", " ")
    assert service.undo_manager.can_revert() is True
    service.feed_character("a")
    assert service.undo_manager.can_revert() is False


def test_manual_backspace_override_prevents_loop(service):
    service.reset()
    service.undo_manager.record_correction("parck", "park", " ")
    service.feed_backspace()
    assert service.manual_override_active is True
    res = service.evaluate_word("parck", delimiter=" ")
    assert res.is_corrected is False
    assert res.corrected_word == "parck"


def test_reset_clears_all_buffers(service):
    service.reset()
    service.feed_character("h")
    service.feed_character("e")
    service.feed_character("y")
    service.reset()
    assert len(service.context_buffer.current_word_chars) == 0


def test_empty_delimiter_commit(service):
    service.reset()
    raw, res = service.handle_delimiter_commit(" ")
    assert raw == ""
    assert res.is_corrected is False


# ==============================================================================
# SECTION 10: 10 20-Word Context Sentences & Long-Range Repetitions
# ==============================================================================
LONG_CONTEXT_CASES = [
    (
        "We held an executive strategy meeting on Monday and we agreed that we will hold another",
        "meat",
        "meet",
    ),
    (
        "I visited the national wildlife conservation park last weekend and I had a wonderful walk in the",
        "parck",
        "park",
    ),
    (
        "The delicious steak at the Italian restaurant was the most tender cut of",
        "meet",
        "meat",
    ),
    (
        "She was looking for her missing leather shoes and finally discovered the second shoe to make a full",
        "pare",
        "pair",
    ),
    (
        "The diplomat negotiated a historic treaty between the two warring nations to finally establish lasting",
        "piece",
        "peace",
    ),
    (
        "After baking the homemade bread in the oven she noticed a fine dust of white",
        "flour",
        "flour",
    ),
    (
        "He drove his vehicle down the mountain road and suddenly had to press firmly on the emergency",
        "break",
        "brake",
    ),
    (
        "The ship captain navigated through dangerous stormy waters across the dark northern",
        "sea",
        "sea",
    ),
    (
        "The tournament championship game ended in victory and the home team celebrated having",
        "won",
        "won",
    ),
    (
        "The construction workers reinforced the towering skyscraper foundation using thousands of tons of structural",
        "steal",
        "steel",
    ),
]


@pytest.mark.parametrize("preceding_20_words, typo, expected", LONG_CONTEXT_CASES)
def test_long_context_20_word_repetition(service, preceding_20_words, typo, expected):
    service.reset()
    for word in preceding_20_words.split():
        for c in word:
            service.feed_character(c)
        service.handle_delimiter_commit(" ")

    for c in typo:
        service.feed_character(c)

    committed, res = service.handle_delimiter_commit(" ")
    assert committed == typo
    if typo == expected:
        assert res.corrected_word.lower() == expected.lower()
    else:
        assert res.is_corrected is True
        assert res.corrected_word.lower() == expected.lower()
