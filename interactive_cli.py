"""
Interactive Live Terminal Runner for AI Autocorrect.
Simulates typing various complex sentences with typos, grammar errors, and Tab reverts.
"""

import sys
import os
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.autocorrect_service import AutocorrectService


def simulate_typing(sentence: str, service: AutocorrectService, should_revert_word: str = None):
    print(f"\nTyping Input: \"{sentence}\"")
    sys.stdout.write("  Live Screen: ")
    sys.stdout.flush()

    service.reset()
    words = sentence.split(" ")
    
    for i, word in enumerate(words):
        if not word:
            continue

        # Type word characters
        for char in word:
            sys.stdout.write(char)
            sys.stdout.flush()
            service.feed_character(char)
            time.sleep(0.015)

        # Hit spacebar
        raw_word, res = service.handle_delimiter_commit(" ")
        if res.is_corrected:
            # Erase original word and print corrected word in green
            sys.stdout.write("\b" * len(raw_word))
            sys.stdout.write(f"\033[92m{res.corrected_word}\033[0m ")
            sys.stdout.flush()
            print(f"\n    └─ [AI Corrected: '{raw_word}' -> '{res.corrected_word}' | Latency: {res.latency_ms:.2f}ms | Conf: {res.confidence:.1%}]")
            sys.stdout.write("  Live Screen: ")
            sys.stdout.flush()

            if should_revert_word and raw_word.lower() == should_revert_word.lower():
                time.sleep(0.3)
                print(f"\n    └─ [Hit TAB key to undo]")
                revert = service.handle_tab_revert()
                if revert:
                    print(f"    └─ \033[93m[Restored original: '{revert[1]}']\033[0m")
                sys.stdout.write("  Live Screen: ")
                sys.stdout.flush()
        else:
            sys.stdout.write(" ")
            sys.stdout.flush()

    print("\n" + "=" * 65)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NeuraType CLI Interactive Typing Simulator")
    parser.add_argument(
        "-c", "--confidence", "--conf",
        type=float,
        default=None,
        help="Custom confidence threshold (e.g. 0.95 or 95). Defaults to 95%.",
    )
    args, _ = parser.parse_known_args()

    conf = args.confidence
    if conf is not None and conf > 1.0:
        conf = conf / 100.0

    service = AutocorrectService(confidence_threshold=conf, revert_timeout=3.5)
    hw = service.onnx_engine.get_hardware_info()

    print("=" * 65)
    print("  🚀 NEURATYPE LIVE ENGINE - CLI TEST RUNNER")
    print(f"  ⚡ Hardware Engine: {hw['active_provider']} (CPU/NPU)")
    print(f"  📦 Model Size:      {hw['model_size_mb']:.2f} MB")
    print(f"  🎯 Confidence Gate: {service.confidence_threshold:.1%}")
    print("=" * 65)

    test_sentences = [
        ("I went to the parck yesterday", None),
        ("She did not recieve my email", None),
        ("That was a very wierd movie", None),
        ("Please check the calender for tomorrow", None),
        ("I bought a pare of shoes at the store", None),
        ("He walked across the feild and stopped", "feild"),
    ]

    for sent, revert_target in test_sentences:
        simulate_typing(sent, service, revert_target)
        time.sleep(0.3)


if __name__ == "__main__":
    main()
