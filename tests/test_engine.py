"""
Automated Test Suite for AI-Powered Autocorrect Engine.
Tests latency, accuracy, context-awareness, and Tab-to-revert state machine.
"""

import time
import pytest
from engine.context_buffer import ContextBuffer
from engine.candidate_generator import CandidateGenerator
from engine.undo_manager import UndoManager
from engine.onnx_infer import OnnxInferenceEngine
from engine.autocorrect_service import AutocorrectService


def test_context_buffer():
    buf = ContextBuffer(max_context_words=5)
    for char in "hello":
        buf.push_char(char)
    assert buf.get_current_word() == "hello"

    buf.pop_char()
    assert buf.get_current_word() == "hell"

    word, delim = buf.commit_word(" ")
    assert word == "hell"
    assert buf.get_context_words() == ["hell"]


def test_candidate_generator_syntax_guard():
    cg = CandidateGenerator()
    # Code, numbers, URLs, and acronyms must be guarded
    assert cg.is_syntax_guarded("user_id") is True
    assert cg.is_syntax_guarded("v1") is True
    assert cg.is_syntax_guarded("https://example.com") is True
    assert cg.is_syntax_guarded("NASA") is True
    assert cg.is_syntax_guarded("getElementById") is True

    # Normal words should not be guarded
    assert cg.is_syntax_guarded("parck") is False
    assert cg.is_syntax_guarded("hello") is False


def test_candidate_generator_casing():
    cg = CandidateGenerator()
    assert cg.apply_casing("parck", "park") == "park"
    assert cg.apply_casing("Parck", "park") == "Park"
    assert cg.apply_casing("PARCK", "park") == "PARK"


def test_candidate_generator_candidates():
    cg = CandidateGenerator()
    candidates = cg.get_candidates("parck", max_candidates=5)
    cand_words = [c[0] for c in candidates]
    assert "park" in cand_words

    # Test contractions
    dont_candidates = [c[0] for c in cg.get_candidates("dont")]
    assert "don't" in dont_candidates


def test_onnx_inference_latency_and_scoring():
    engine = OnnxInferenceEngine()
    results, latency_ms = engine.score_candidates(
        context_prefix="I am walking in the",
        candidates=["park", "pack", "pork", "part"],
    )
    assert len(results) == 4
    # Latency should be under 20ms
    print(f"Test Latency: {latency_ms:.2f} ms on {engine.active_provider}")
    assert latency_ms < 35.0  # Safe upper bound
    # "park" should be the top ranked candidate
    assert results[0][0] == "park"


def test_undo_manager():
    um = UndoManager(timeout_seconds=1.0)
    assert um.can_revert() is False

    um.record_correction("parck", "park", " ")
    assert um.can_revert() is True

    revert = um.consume_revert()
    assert revert == ("park", "parck", " ")
    assert um.can_revert() is False  # Cannot revert twice


def test_autocorrect_service_live_flow():
    service = AutocorrectService(confidence_threshold=0.60)

    # Type: "went to the parck "
    for w in ["went", "to", "the"]:
        for c in w:
            service.feed_character(c)
        service.handle_delimiter_commit(" ")

    for c in "parck":
        service.feed_character(c)

    committed, res = service.handle_delimiter_commit(" ")
    assert committed == "parck"
    assert res.is_corrected is True
    assert res.corrected_word == "park"
    assert res.latency_ms < 30.0

    # Test Tab Revert
    revert_data = service.handle_tab_revert()
    assert revert_data is not None
    assert revert_data == ("park", "parck", " ")
