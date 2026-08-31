"""
Undo / Revert Manager for Tab-to-Revert Autocorrect Mechanics.
Maintains state machine and monotonic expiration timers.
"""

import time
from typing import Optional, Tuple


class UndoManager:
    """
    Tracks the most recent autocorrect event and manages the
    instant Tab-to-revert state lifecycle.
    """

    def __init__(self, timeout_seconds: float = 3.5):
        self.timeout_seconds = timeout_seconds
        self.original_word: str = ""
        self.corrected_word: str = ""
        self.delimiter: str = " "
        self.timestamp: float = 0.0
        self.is_active: bool = False

    def record_correction(
        self, original_word: str, corrected_word: str, delimiter: str = " "
    ) -> None:
        """Arms the undo state with the latest correction."""
        self.original_word = original_word
        self.corrected_word = corrected_word
        self.delimiter = delimiter
        self.timestamp = time.monotonic()
        self.is_active = True

    def can_revert(self) -> bool:
        """Returns True if the undo state is valid and within timeout."""
        if not self.is_active:
            return False
        elapsed = time.monotonic() - self.timestamp
        return elapsed <= self.timeout_seconds

    def consume_revert(self) -> Optional[Tuple[str, str, str]]:
        """
        Consumes the undo state and returns:
            (corrected_word_to_erase, original_word_to_restore, delimiter)
        Disarms the undo state so Tab cannot be triggered twice.
        """
        if not self.can_revert():
            return None

        result = (self.corrected_word, self.original_word, self.delimiter)
        self.invalidate()
        return result

    def invalidate(self) -> None:
        """Disarms the undo state (e.g. when typing continues)."""
        self.is_active = False
        self.original_word = ""
        self.corrected_word = ""
        self.timestamp = 0.0

    def get_status_text(self) -> str:
        """Human-readable status for telemetry UI."""
        if self.can_revert():
            remaining = max(0.0, self.timeout_seconds - (time.monotonic() - self.timestamp))
            return f"Armed: Press [TAB] to revert '{self.corrected_word}' -> '{self.original_word}' ({remaining:.1f}s left)"
        return "Idle (No active undo)"
