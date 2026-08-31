"""
Global Windows Keyboard Hook Service for AI-Powered Autocorrect.
Includes safety controls: Hotkey toggle (Ctrl+Alt+A) and Emergency Kill-switch (Ctrl+Alt+Q).
"""

import sys
import os
import time
import threading
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Controller

# Add parent directory to path so engine can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.autocorrect_service import AutocorrectService, CorrectionResult


class GlobalAutocorrectHook:
    def __init__(self):
        print("=" * 60)
        print("  AI-POWERED LOCAL LIVE AUTOCORRECT - WINDOWS GLOBAL HOOK")
        print("=" * 60)
        print("  Controls:")
        print("    [Ctrl + Alt + A] : Toggle Global Autocorrect ON / OFF")
        print("    [Ctrl + Alt + Q] : Emergency Exit / Stop Service")
        print("    [Tab]            : Instant Revert Last Correction")
        print("=" * 60)

        self.service = AutocorrectService(confidence_threshold=0.65, revert_timeout=3.5)
        self.keyboard_controller = Controller()
        self.is_enabled = True
        self.is_running = True

        # State tracking to prevent infinite loops from simulated keystrokes
        self.is_simulating_input = False
        self.ctrl_pressed = False
        self.alt_pressed = False

    def on_press(self, key):
        if not self.is_running or self.is_simulating_input:
            return

        # 1. Track Modifiers
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            self.ctrl_pressed = True
            return
        if key in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
            self.alt_pressed = True
            return

        # 2. Check Global Hotkeys
        if self.ctrl_pressed and self.alt_pressed:
            if hasattr(key, "char") and key.char:
                if key.char.lower() == "a":
                    self.is_enabled = not self.is_enabled
                    state = "ENABLED (Active)" if self.is_enabled else "PAUSED (Disabled)"
                    print(f"\n[HOTKEY] Global Autocorrect is now: {state}")
                    self.service.reset()
                    return
                elif key.char.lower() == "q":
                    print("\n[HOTKEY] Emergency Exit Triggered. Stopping Service...")
                    self.is_running = False
                    return False  # Stops listener

        # If globally disabled, do not process
        if not self.is_enabled:
            return

        # 3. Handle TAB (Revert Trigger)
        if key == Key.tab:
            revert = self.service.handle_tab_revert()
            if revert:
                corrected, original, delim = revert
                print(f"[REVERT] Restoring '{corrected}' -> '{original}'")
                self._dispatch_revert(corrected, original, delim)
            return

        # 4. Handle Backspace
        if key == Key.backspace:
            self.service.feed_backspace()
            return

        # 5. Handle Delimiters (Space, Enter)
        if key == Key.space:
            self._handle_delimiter(" ")
            return
        if key == Key.enter:
            self._handle_delimiter("\n")
            return

        # 6. Handle Printable Characters
        if hasattr(key, "char") and key.char:
            char = key.char
            if char in (".", ",", "!", "?", ";", ":"):
                self._handle_delimiter(char)
            elif char.isprintable():
                self.service.feed_character(char)

    def on_release(self, key):
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            self.ctrl_pressed = False
        if key in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
            self.alt_pressed = False

    def _handle_delimiter(self, delimiter: str):
        committed_word, result = self.service.handle_delimiter_commit(delimiter)
        if result.is_corrected:
            print(f"[AUTOCORRECT] {result.explanation} | Latency: {result.latency_ms:.2f}ms")
            self._dispatch_replacement(result.original_word, result.corrected_word, delimiter)

    def _dispatch_replacement(self, original: str, corrected: str, delimiter: str):
        """Atomically erases original word + delimiter and types corrected word + delimiter."""
        self.is_simulating_input = True
        try:
            # Erase original word length + 1 (for the delimiter that was just typed)
            erase_count = len(original) + len(delimiter)
            for _ in range(erase_count):
                self.keyboard_controller.press(Key.backspace)
                self.keyboard_controller.release(Key.backspace)
                time.sleep(0.001)

            # Type corrected word + delimiter
            self.keyboard_controller.type(f"{corrected}{delimiter}")
        finally:
            self.is_simulating_input = False

    def _dispatch_revert(self, corrected: str, original: str, delimiter: str):
        """Atomically erases corrected word + delimiter and restores original typo."""
        self.is_simulating_input = True
        try:
            # Erase corrected word + delimiter length
            erase_count = len(corrected) + len(delimiter)
            for _ in range(erase_count):
                self.keyboard_controller.press(Key.backspace)
                self.keyboard_controller.release(Key.backspace)
                time.sleep(0.001)

            # Type original typo + delimiter
            self.keyboard_controller.type(f"{original}{delimiter}")
        finally:
            self.is_simulating_input = False

    def run(self):
        print(f"\n[STATUS] Global Hook Active across Windows.")
        print(f"[STATUS] Hardware Acceleration: {self.service.onnx_engine.active_provider}")
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()


def main():
    hook = GlobalAutocorrectHook()
    hook.run()


if __name__ == "__main__":
    main()
