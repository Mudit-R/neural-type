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
from engine.policy_config import PolicyConfig


class GlobalAutocorrectHook:
    def __init__(self, policy: PolicyConfig = None):
        print("=" * 60, flush=True)
        print("  AI-POWERED LOCAL LIVE AUTOCORRECT - WINDOWS GLOBAL HOOK", flush=True)
        print("=" * 60, flush=True)
        print("  Controls:", flush=True)
        print("    [Ctrl + Alt + A] : Toggle Global Autocorrect ON / OFF", flush=True)
        print("    [Ctrl + Alt + Q] : Emergency Exit / Stop Service", flush=True)
        print("    [Tab]            : Instant Revert Last Correction", flush=True)
        print("=" * 60, flush=True)

        self.policy = policy or PolicyConfig()
        self.service = AutocorrectService(policy=self.policy)
        self.keyboard_controller = Controller()
        self.is_enabled = self.policy.is_hook_enabled()
        self.is_running = True
        self.is_simulating_input = False
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.last_active_proc = ""

    def _get_active_process_name(self) -> str:
        """Retrieves the process executable name of the current foreground window."""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return ""
            pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == 0:
                return ""
            # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h_proc = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid.value)
            if not h_proc:
                return ""
            buf = ctypes.create_unicode_buffer(512)
            size = wintypes.DWORD(512)
            exe_name = ""
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                full_path = buf.value
                exe_name = os.path.basename(full_path).lower()
            ctypes.windll.kernel32.CloseHandle(h_proc)
            return exe_name
        except Exception:
            return ""

    def on_press(self, key, injected=False):
        # Ignore synthetic/simulated keystrokes or while service is paused/busy
        if injected or not self.is_running or self.is_simulating_input:
            return

        # Check enterprise policy hook status
        if not self.policy.is_hook_enabled():
            return

        # Check application switch & allowlist / denylist
        active_proc = self._get_active_process_name()
        if active_proc != self.last_active_proc:
            self.last_active_proc = active_proc
            self.service.context_buffer.current_word_chars.clear()
            self.service.undo_manager.invalidate()

        if active_proc and not self.policy.is_app_allowed(active_proc):
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
                    print(f"\n[HOTKEY] Global Autocorrect is now: {state}", flush=True)
                    self.service.reset()
                    return
                elif key.char.lower() == "q":
                    print("\n[HOTKEY] Emergency Exit Triggered. Stopping Service...", flush=True)
                    self.is_running = False
                    return False  # Stops listener

        # If globally disabled, do not process
        if not self.is_enabled:
            return

        # 3. Handle TAB fallback
        if key == Key.tab:
            revert = self.service.handle_tab_revert()
            if revert:
                corrected, original, delim = revert
                print(f"[REVERT] Restoring '{corrected}' -> '{original}'", flush=True)
                self._dispatch_revert(corrected, original, delim)
            return

        # 3b. Support Ctrl+Z for instant undo
        if self.ctrl_pressed and hasattr(key, "char") and key.char and key.char.lower() == "z":
            if self.service.undo_manager.can_revert():
                revert = self.service.handle_tab_revert()
                if revert:
                    corrected, original, delim = revert
                    print(f"[REVERT] Restoring '{corrected}' -> '{original}' (Ctrl+Z triggered)", flush=True)
                    self._dispatch_revert(corrected, original, delim)
                return

        # 4. Handle Backspace
        if key == Key.backspace:
            self.service.feed_backspace()
            return

        # 5. Handle Navigation / Cursor movement (resets active word buffer)
        if key in (
            Key.left, Key.right, Key.up, Key.down,
            Key.home, Key.end, Key.page_up, Key.page_down,
            Key.esc, Key.delete
        ):
            self.service.context_buffer.current_word_chars.clear()
            self.service.undo_manager.invalidate()
            return

        # 6. Handle Delimiters (Space, Enter)
        if key == Key.space:
            self._handle_delimiter(" ")
            return
        if key == Key.enter:
            self._handle_delimiter("\n")
            return

        # 7. Handle Printable Characters
        if hasattr(key, "char") and key.char:
            char = key.char
            if char in (".", ",", "!", "?", ";", ":"):
                self._handle_delimiter(char)
            elif char.isprintable():
                self.service.feed_character(char)

    def on_release(self, key, injected=False):
        if injected:
            return
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            self.ctrl_pressed = False
        if key in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
            self.alt_pressed = False

    def win32_event_filter(self, msg, data):
        """
        Windows Low-Level Keyboard Event Filter (WH_KEYBOARD_LL).
        Intercepts and suppresses keys at the OS driver level before applications receive them.
        When Tab is pressed while an autocorrect revert is armed, we swallow the Tab key
        so the foreground application (Chrome, Notepad, MS Word) does NOT shift focus, insert tabs, or navigate.
        """
        # data.vkCode 0x09 is VK_TAB
        # msg 256 is WM_KEYDOWN, 260 is WM_SYSKEYDOWN
        if data.vkCode == 0x09:
            if self.service.undo_manager.can_revert():
                if msg in (256, 260):
                    revert = self.service.handle_tab_revert()
                    if revert:
                        corrected, original, delim = revert
                        print(f"[REVERT] Restoring '{corrected}' -> '{original}' (Tab intercepted & suppressed)", flush=True)
                        self._dispatch_revert(corrected, original, delim)
                # Suppress the Tab key from Windows OS event queue
                return False

        return True

    def _handle_delimiter(self, delimiter: str):
        committed_word, result = self.service.handle_delimiter_commit(delimiter)
        if result.is_corrected:
            print(f"[AUTOCORRECT] {result.explanation} | Latency: {result.latency_ms:.2f}ms", flush=True)
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
                time.sleep(0.002)

            time.sleep(0.005)
            # Type corrected word + delimiter
            self.keyboard_controller.type(f"{corrected}{delimiter}")
            time.sleep(0.015)
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
                time.sleep(0.002)

            time.sleep(0.005)
            # Type original typo + delimiter
            self.keyboard_controller.type(f"{original}{delimiter}")
            time.sleep(0.015)
        finally:
            self.is_simulating_input = False

    def run(self):
        print(f"\n[STATUS] Global Hook Active across Windows.", flush=True)
        print(f"[STATUS] Hardware Acceleration: {self.service.onnx_engine.active_provider}", flush=True)
        print(f"[READY] Type in any application (Notepad, Word, Chrome). Try: 'went to the parck '\n", flush=True)
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
            win32_event_filter=self.win32_event_filter,
        ) as listener:
            listener.join()


def main():
    hook = GlobalAutocorrectHook()
    hook.run()


if __name__ == "__main__":
    main()

