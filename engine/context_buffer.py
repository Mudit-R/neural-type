"""
Context Ring Buffer for Tracking User Keystrokes and Rolling Sentence Context.
Maintains a rolling window of recent words and the active word buffer.
"""

from collections import deque
from typing import List, Optional, Tuple


class ContextBuffer:
    """
    Thread-safe context buffer maintaining the last N words (up to 25 words)
    and current active in-flight word characters.
    """

    def __init__(self, max_context_words: int = 25):
        self.max_context_words = max_context_words
        self.history: deque[str] = deque(maxlen=max_context_words)
        self.current_word_chars: List[str] = []

    def push_char(self, char: str) -> None:
        """Appends an alphanumeric or valid word character to the current word."""
        self.current_word_chars.append(char)

    def pop_char(self) -> Optional[str]:
        """Handles Backspace by removing the last typed character."""
        if self.current_word_chars:
            return self.current_word_chars.pop()
        return None

    def get_current_word(self) -> str:
        """Returns the currently typed in-flight word."""
        return "".join(self.current_word_chars)

    def is_empty(self) -> bool:
        """Checks if current in-flight word buffer is empty."""
        return len(self.current_word_chars) == 0

    def commit_word(self, delimiter: str = " ") -> Tuple[str, str]:
        """
        Commits the current word into history upon hitting a delimiter.
        Returns (committed_word, delimiter).
        """
        word = self.get_current_word()
        self.current_word_chars.clear()
        if word:
            self.history.append(word)
        return word, delimiter

    def update_last_history_word(self, old_word: str, new_word: str) -> bool:
        """
        Updates the last committed word in history if it was autocorrected.
        """
        if self.history and self.history[-1] == old_word:
            self.history[-1] = new_word
            return True
        return False

    def get_context_words(self, count: Optional[int] = None) -> List[str]:
        """Returns the list of recent context words up to `count`."""
        if count is None or count >= len(self.history):
            return list(self.history)
        return list(self.history)[-count:]

    def get_context_string(self, count: int = 20) -> str:
        """
        Returns the recent context words as a single string (up to 20 words).
        """
        words = self.get_context_words(count)
        if not words:
            return ""
        return " ".join(words)

    def clear(self) -> None:
        """Resets both in-flight buffer and history."""
        self.history.clear()
        self.current_word_chars.clear()
