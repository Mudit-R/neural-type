"""
Interactive Desktop Sandbox GUI for AI-Powered Local Live Autocorrect.
Provides an isolated, 100% safe testing environment with real-time telemetry.
"""

import sys
import os
import time
import tkinter as tk
from tkinter import ttk, font
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.autocorrect_service import AutocorrectService, CorrectionResult


class AutocorrectSandboxGUI:
    def __init__(self, root, confidence_threshold=None):
        self.root = root
        self.root.title("NeuraType - Safe Sandbox Testbed")
        self.root.geometry("960x700")
        self.root.minsize(800, 600)
        self.root.configure(bg="#121214")

        eff_conf = confidence_threshold
        if eff_conf is not None and eff_conf > 1.0:
            eff_conf = eff_conf / 100.0

        # Initialize Autocorrect Engine
        self.service = AutocorrectService(confidence_threshold=eff_conf, revert_timeout=3.5)
        self.hw_info = self.service.onnx_engine.get_hardware_info()

        # Stats
        self.total_corrections = 0
        self.total_reverts = 0

        self._setup_styles()
        self._build_ui()
        self._bind_events()
        self._start_status_poller()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Color Palette
        self.bg_dark = "#121214"
        self.card_bg = "#1e1e24"
        self.border_col = "#2e2e38"
        self.accent_blue = "#3b82f6"
        self.accent_green = "#10b981"
        self.accent_amber = "#f59e0b"
        self.text_primary = "#f3f4f6"
        self.text_secondary = "#9ca3af"

        self.font_title = ("Segoe UI", 16, "bold")
        self.font_body = ("Segoe UI", 11)
        self.font_mono = ("Consolas", 11)
        self.font_editor = ("Consolas", 14)

    def _build_ui(self):
        # 1. Header Bar
        header_frame = tk.Frame(self.root, bg=self.card_bg, highlightthickness=1, highlightbackground=self.border_col)
        header_frame.pack(fill=tk.X, padx=16, pady=(16, 8))

        title_lbl = tk.Label(
            header_frame,
            text="AI-Powered Local Live Autocorrect (NPU / CPU)",
            font=self.font_title,
            fg=self.text_primary,
            bg=self.card_bg,
            padx=14,
            pady=10,
        )
        title_lbl.pack(side=tk.LEFT)

        dev_name = self.hw_info["active_provider"].replace("ExecutionProvider", "")
        is_npu = self.hw_info["is_npu_or_gpu"]
        badge_text = f"Engine: {dev_name} ({'NPU/GPU' if is_npu else 'CPU AVX2'})"
        badge_color = self.accent_green if is_npu else self.accent_blue

        self.hw_badge = tk.Label(
            header_frame,
            text=badge_text,
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg=badge_color,
            padx=10,
            pady=4,
            relief=tk.FLAT,
        )
        self.hw_badge.pack(side=tk.RIGHT, padx=14, pady=10)

        # 2. Main Editor Card
        editor_card = tk.Frame(self.root, bg=self.card_bg, highlightthickness=1, highlightbackground=self.border_col)
        editor_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        editor_header = tk.Frame(editor_card, bg=self.card_bg)
        editor_header.pack(fill=tk.X, padx=12, pady=(10, 4))

        tk.Label(
            editor_header,
            text="Live Typing Sandbox (Type sentences with typos; hit Space to autocorrect, Tab to revert):",
            font=self.font_body,
            fg=self.text_secondary,
            bg=self.card_bg,
        ).pack(side=tk.LEFT)

        clear_btn = tk.Button(
            editor_header,
            text="Clear Editor",
            font=("Segoe UI", 9),
            bg="#2e2e38",
            fg=self.text_primary,
            activebackground="#3e3e4a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=8,
            pady=2,
            command=self._clear_editor,
        )
        clear_btn.pack(side=tk.RIGHT, padx=4)

        sample_btn = tk.Button(
            editor_header,
            text="Load Sample Typos",
            font=("Segoe UI", 9),
            bg="#2e2e38",
            fg=self.accent_blue,
            activebackground="#3e3e4a",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=8,
            pady=2,
            command=self._load_sample,
        )
        sample_btn.pack(side=tk.RIGHT, padx=4)

        # Text Area
        self.text_editor = tk.Text(
            editor_card,
            bg="#16161a",
            fg=self.text_primary,
            insertbackground="#ffffff",
            font=self.font_editor,
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=14,
            pady=14,
            undo=True,
            highlightthickness=1,
            highlightbackground=self.border_col,
            highlightcolor=self.accent_blue,
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # 3. Telemetry & Metric Strip
        telemetry_frame = tk.Frame(self.root, bg=self.card_bg, highlightthickness=1, highlightbackground=self.border_col)
        telemetry_frame.pack(fill=tk.X, padx=16, pady=4)

        self.latency_lbl = tk.Label(
            telemetry_frame,
            text="Latency: -- ms",
            font=("Segoe UI", 10, "bold"),
            fg=self.accent_green,
            bg=self.card_bg,
            padx=12,
            pady=8,
        )
        self.latency_lbl.pack(side=tk.LEFT)

        self.conf_lbl = tk.Label(
            telemetry_frame,
            text="Confidence: -- %",
            font=("Segoe UI", 10),
            fg=self.text_primary,
            bg=self.card_bg,
            padx=12,
            pady=8,
        )
        self.conf_lbl.pack(side=tk.LEFT)

        self.undo_lbl = tk.Label(
            telemetry_frame,
            text="Tab Revert: Idle",
            font=("Segoe UI", 10),
            fg=self.text_secondary,
            bg=self.card_bg,
            padx=12,
            pady=8,
        )
        self.undo_lbl.pack(side=tk.LEFT)

        self.stats_lbl = tk.Label(
            telemetry_frame,
            text="Corrections: 0 | Reverts: 0",
            font=("Segoe UI", 10),
            fg=self.text_secondary,
            bg=self.card_bg,
            padx=12,
            pady=8,
        )
        self.stats_lbl.pack(side=tk.LEFT)

        # Confidence Filter Adjustment Slider
        slider_frame = tk.Frame(telemetry_frame, bg=self.card_bg)
        slider_frame.pack(side=tk.RIGHT, padx=12, pady=4)

        tk.Label(
            slider_frame,
            text="Filter Conf:",
            font=("Segoe UI", 9),
            fg=self.text_secondary,
            bg=self.card_bg,
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.conf_slider = tk.Scale(
            slider_frame,
            from_=50,
            to=99,
            orient=tk.HORIZONTAL,
            showvalue=0,
            bg=self.card_bg,
            troughcolor="#121214",
            activebackground=self.accent_blue,
            highlightthickness=0,
            command=self._on_slider_change,
            length=90,
        )
        self.conf_slider.set(int(self.service.confidence_threshold * 100))
        self.conf_slider.pack(side=tk.LEFT, padx=2)

        self.conf_slider_lbl = tk.Label(
            slider_frame,
            text=f"{int(self.service.confidence_threshold * 100)}%",
            font=("Segoe UI", 9, "bold"),
            fg=self.accent_blue,
            bg=self.card_bg,
            width=4,
        )
        self.conf_slider_lbl.pack(side=tk.LEFT)

        # 4. Event Log Card
        log_card = tk.Frame(self.root, bg=self.card_bg, highlightthickness=1, highlightbackground=self.border_col)
        log_card.pack(fill=tk.X, padx=16, pady=(4, 16))

        tk.Label(
            log_card,
            text="Real-Time Correction Event Stream:",
            font=("Segoe UI", 10, "bold"),
            fg=self.text_secondary,
            bg=self.card_bg,
        ).pack(anchor=tk.W, padx=12, pady=(6, 2))

        self.log_list = tk.Listbox(
            log_card,
            bg="#16161a",
            fg=self.text_primary,
            font=self.font_mono,
            height=4,
            relief=tk.FLAT,
            highlightthickness=0,
            selectbackground="#2e2e38",
        )
        self.log_list.pack(fill=tk.X, padx=12, pady=(0, 8))
        self._add_log("Sandbox Engine initialized. Type in the box above.")

    def _bind_events(self):
        self.text_editor.bind("<Key>", self._on_key_press)

    def _on_key_press(self, event: tk.Event):
        # 1. Handle TAB Key (Revert Trigger)
        if event.keysym == "Tab":
            revert = self.service.handle_tab_revert()
            if revert:
                corrected, original, delim = revert
                self._revert_in_editor(corrected, original, delim)
                self.total_reverts += 1
                self._update_stats()
                self._add_log(f"REVERT TRIGGERED via [TAB]: Restored '{corrected}' -> '{original}'")
                return "break"
            else:
                return None

        # 2. Handle Backspace Key
        if event.keysym == "BackSpace":
            self.service.feed_backspace()
            return None

        # 3. Handle Delimiters (Space, Enter, Period, Comma, etc.)
        if event.char in (" ", "\r", "\n", ".", ",", "!", "?"):
            delim = "\n" if event.char == "\r" else event.char
            
            raw_word, res = self.service.handle_delimiter_commit(delimiter=delim)

            # Update Telemetry Display
            self.latency_lbl.config(text=f"Latency: {res.latency_ms:.2f} ms")
            self.conf_lbl.config(text=f"Confidence: {res.confidence * 100:.1f}%")

            if res.is_corrected:
                self._replace_last_word_in_editor(raw_word, res.corrected_word, delim)
                self.total_corrections += 1
                self._update_stats()
                self._add_log(f"CORRECTED: '{raw_word}' -> '{res.corrected_word}' ({res.latency_ms:.2f}ms, {res.confidence * 100:.1f}%)")
                return "break"

            return None

        # 4. Standard Character Input
        if event.char and event.char.isprintable():
            self.service.feed_character(event.char)

        return None

    def _replace_last_word_in_editor(self, original: str, corrected: str, delim: str):
        pos = self.text_editor.index(tk.INSERT)
        
        erase_start = f"{pos} - {len(original)} chars"
        self.text_editor.delete(erase_start, pos)
        self.text_editor.insert(erase_start, corrected + delim)

    def _revert_in_editor(self, corrected: str, original: str, delim: str):
        pos = self.text_editor.index(tk.INSERT)
        total_len = len(corrected) + len(delim)
        erase_start = f"{pos} - {total_len} chars"
        self.text_editor.delete(erase_start, pos)
        self.text_editor.insert(erase_start, original + delim)

    def _update_stats(self):
        self.stats_lbl.config(
            text=f"Corrections: {self.total_corrections} | Reverts: {self.total_reverts}"
        )

    def _add_log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.log_list.insert(0, entry)
        if self.log_list.size() > 50:
            self.log_list.delete(tk.END)

    def _clear_editor(self):
        self.text_editor.delete("1.0", tk.END)
        self.service.reset()
        self.latency_lbl.config(text="Latency: -- ms")
        self.conf_lbl.config(text="Confidence: -- %")
        self.undo_lbl.config(text="Tab Revert: Idle", fg=self.text_secondary)
        self._add_log("Editor cleared.")

    def _load_sample(self):
        sample = "I want to go to the parck "
        self.text_editor.delete("1.0", tk.END)
        self.service.reset()

        for char in sample:
            if char == " ":
                raw_word, res = self.service.handle_delimiter_commit(delimiter=" ")
                if res.is_corrected:
                    self.text_editor.insert(tk.END, res.corrected_word + " ")
                    self.total_corrections += 1
                    self._update_stats()
                    self._add_log(f"Sample loaded: Corrected '{raw_word}' -> '{res.corrected_word}'")
                else:
                    self.text_editor.insert(tk.END, " ")
            else:
                self.text_editor.insert(tk.END, char)
                self.service.feed_character(char)

        self.text_editor.focus_set()
        self.text_editor.mark_set(tk.INSERT, tk.END)

    def _start_status_poller(self):
        def poll():
            while True:
                time.sleep(0.2)
                try:
                    if self.service.undo_manager.is_active():
                        rem = self.service.undo_manager.remaining_time()
                        self.root.after(0, lambda r=rem: self.undo_lbl.config(
                            text=f"Tab Revert: Armed ({r:.1f}s)",
                            fg=self.accent_amber
                        ))
                    else:
                        self.root.after(0, lambda: self.undo_lbl.config(
                            text="Tab Revert: Idle",
                            fg=self.text_secondary
                        ))
                except Exception:
                    pass

    def _on_slider_change(self, val):
        try:
            int_val = int(val)
            self.service.confidence_threshold = int_val / 100.0
            if hasattr(self, "conf_slider_lbl"):
                self.conf_slider_lbl.config(text=f"{int_val}%")
        except Exception:
            pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NeuraType Desktop Sandbox GUI")
    parser.add_argument(
        "-c", "--confidence", "--conf",
        type=float,
        default=None,
        help="Custom confidence threshold (e.g. 0.95 or 95). Defaults to policy.yaml value.",
    )
    args, _ = parser.parse_known_args()

    root = tk.Tk()
    app = AutocorrectSandboxGUI(root, confidence_threshold=args.confidence)
    root.mainloop()


if __name__ == "__main__":
    main()
