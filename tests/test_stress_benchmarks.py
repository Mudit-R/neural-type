"""
Production-Grade Stress and Benchmark Test Suite for Autocorrect Engine.
Simulates high-speed human typing (120+ WPM), verifies P50/P95/P99 latencies,
tests 20-word context sentences and real-word confusable error detection.
"""

import time
import random
import numpy as np
import pytest
from engine.autocorrect_service import AutocorrectService


@pytest.fixture(scope="module")
def service():
    return AutocorrectService(confidence_threshold=0.60, revert_timeout=3.5)


def test_edge_case_and_real_word_corpus(service):
    """
    Validates corrections across real-world typos, homophones, and real-word confusions.
    """
    test_cases = [
        # (context, typo_to_type, expected_correction, should_correct)
        ("I went to the", "parck", "park", True),
        ("He walked into the", "feild", "field", True),
        ("I will", "definately", "definitely", True),
        ("She did not", "recieve", "receive", True),
        ("That was very", "wierd", "weird", True),
        ("Please check the", "calender", "calendar", True),
        ("I bought a", "pare", "pair", True),             # Real-word confusable
        ("I will", "meat", "meet", True),                 # Real-word confusable (meat vs meet)
        ("I ate a", "peace", "piece", True),              # Real-word confusable (peace vs piece)
        ("They are over", "there", "there", False),       # Already correct
        ("Look at that", "theyre", "they're", True),      # Contraction
        ("I", "dont", "don't", True),                     # Contraction
        ("I", "cant", "can't", True),                     # Contraction
        ("Programming in", "Python3", "Python3", False),  # Syntax guarded (digit)
        ("Check variable", "user_id", "user_id", False),  # Syntax guarded (underscore)
        ("Visit", "https://google.com", "https://google.com", False),  # URL guarded
    ]

    passed = 0
    for ctx, typo, expected, should_correct in test_cases:
        service.reset()
        # Seed context
        for word in ctx.split():
            for c in word:
                service.feed_character(c)
            service.handle_delimiter_commit(" ")

        # Type the target word
        for c in typo:
            service.feed_character(c)

        committed, res = service.handle_delimiter_commit(" ")
        assert committed == typo

        if should_correct:
            assert res.is_corrected is True, f"Failed to correct '{typo}' in context '{ctx}'"
            assert res.corrected_word.lower() == expected.lower(), f"Expected '{expected}', got '{res.corrected_word}'"
        else:
            assert res.is_corrected is False, f"Should not have corrected '{typo}'"

        passed += 1

    print(f"\n[Test] Real-word and edge case corpus passed: {passed}/{len(test_cases)} tests.")


def test_20_word_long_context(service):
    """
    Validates that a full 20-word preceding context is preserved and used for scoring.
    """
    service.reset()
    long_sentence = (
        "Yesterday when the weather was sunny and warm we decided to take our bicycle for a long ride to the"
    )
    for word in long_sentence.split():
        for c in word:
            service.feed_character(c)
        service.handle_delimiter_commit(" ")

    assert len(service.context_buffer.history) >= 19

    # Type typo: 'parck'
    for c in "parck":
        service.feed_character(c)

    committed, res = service.handle_delimiter_commit(" ")
    assert committed == "parck"
    assert res.is_corrected is True
    assert res.corrected_word == "park"
    assert res.latency_ms < 15.0


def test_high_speed_burst_typing_stress(service):
    """
    Simulates rapid continuous typing of 250 words (equivalent to 150 WPM)
    and verifies latency distribution (P50, P95, P99).
    """
    words = [
        "the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog",
        "parck", "feild", "definately", "recieve", "wierd", "calender", "dont",
        "apple", "banana", "computer", "keyboard", "windows", "system", "local",
        "theyre", "cant", "wont", "going", "tomorrow", "yesterday", "morning"
    ]

    latencies = []
    service.reset()

    t_start = time.perf_counter()
    for i in range(250):
        w = random.choice(words)
        # Type chars
        for c in w:
            service.feed_character(c)
        # Hit space
        committed, res = service.handle_delimiter_commit(" ")
        latencies.append(res.latency_ms)

    total_time = (time.perf_counter() - t_start) * 1000.0

    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    avg_latency = np.mean(latencies)

    print(f"\n[Benchmark] 250-Word Stress Test Results:")
    print(f"  - Total Elapsed Time: {total_time:.2f} ms")
    print(f"  - Average Latency:    {avg_latency:.2f} ms")
    print(f"  - P50 (Median):       {p50:.2f} ms")
    print(f"  - P95:                {p95:.2f} ms")
    print(f"  - P99:                {p99:.2f} ms")

    assert p50 < 8.0
    assert p95 < 20.0
    assert p99 < 35.0


def test_tab_revert_rapid_sequence(service):
    """
    Tests rapid alternating correction and Tab-revert sequences.
    """
    service.reset()
    for _ in range(10):
        for c in "parck":
            service.feed_character(c)
        committed, res = service.handle_delimiter_commit(" ")
        assert res.is_corrected is True
        assert res.corrected_word == "park"

        revert = service.handle_tab_revert()
        assert revert is not None
        assert revert[0] == "park"
        assert revert[1] == "parck"
        assert service.handle_tab_revert() is None
