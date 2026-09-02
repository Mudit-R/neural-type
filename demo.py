"""
Interactive Live Demo Simulator for AI-Powered Autocorrect.
Simulates realistic keystrokes, demonstrates live spacebar correction,
Tab-to-revert mechanics, and prints real-time hardware telemetry.
"""

import sys
import os
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.autocorrect_service import AutocorrectService


def run_demo():
    print("\n" + "=" * 70)
    print("  [AI-POWERED LOCAL LIVE AUTOCORRECT - INTERACTIVE DEMO]")
    print("=" * 70)

    service = AutocorrectService(confidence_threshold=0.95, revert_timeout=3.5)
    hw = service.onnx_engine.get_hardware_info()

    print(f"  * Hardware Engine: {hw['active_provider']} ({'NPU/GPU' if hw['is_npu_or_gpu'] else 'CPU AVX2'})")
    print(f"  * Model Size:      {hw['model_size_mb']:.2f} MB (INT8 Quantized)")
    print("=" * 70 + "\n")

    scenarios = [
        {
            "description": "Demo 1: Contextual Typo ('parck' -> 'park')",
            "sentence": "I want to go to the parck ",
            "test_revert": False,
        },
        {
            "description": "Demo 2: Contractions & Missing Apostrophes ('dont' -> 'don't')",
            "sentence": "I dont know what happened ",
            "test_revert": False,
        },
        {
            "description": "Demo 3: Contextual Homophone ('pare' of shoes -> 'pair')",
            "sentence": "I bought a pare of shoes ",
            "test_revert": False,
        },
        {
            "description": "Demo 4: Autocorrect + Instant TAB Revert ('feild' -> 'field' -> Tab reverts to 'feild')",
            "sentence": "He walked across the feild ",
            "test_revert": True,
        },
    ]

    for sc in scenarios:
        print(f"-> {sc['description']}")
        service.reset()

        tokens = sc["sentence"].split(" ")
        for i, word in enumerate(tokens):
            if not word:
                continue

            # Simulate typing characters
            for char in word:
                sys.stdout.write(char)
                sys.stdout.flush()
                service.feed_character(char)
                time.sleep(0.01)

            # Hit spacebar delimiter
            raw_word, res = service.handle_delimiter_commit(" ")
            if res.is_corrected:
                sys.stdout.write(f" -> [{res.corrected_word.upper()}] ")
                sys.stdout.flush()
                print(f" <-- [AUTO-CORRECT: '{raw_word}' -> '{res.corrected_word}' | Latency: {res.latency_ms:.2f}ms | Conf: {res.confidence:.1%}]")
            else:
                sys.stdout.write(" ")
                sys.stdout.flush()

        if sc["test_revert"]:
            time.sleep(0.2)
            print("   [KEYBOARD EVENT: USER PRESSES TAB KEY TO REVERT]")
            revert = service.handle_tab_revert()
            if revert:
                corrected, original, delim = revert
                print(f"   [REVERTED: Restored original typo '{original}']")

        print("\n" + "-" * 70 + "\n")
        time.sleep(0.3)

    print("[SUCCESS] Demo finished. Launch the desktop GUI anytime with: .venv\\Scripts\\python run_sandbox.py\n")


if __name__ == "__main__":
    run_demo()
