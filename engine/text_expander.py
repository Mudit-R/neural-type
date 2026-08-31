"""
Smart Text Expander & Variable Template Engine.
Provides sub-0.1ms expansion of //keyword triggers into rich multi-line templates.
"""

import re
import datetime
from typing import Optional, Dict, Any


class TextExpander:
    """
    High-performance snippet expansion engine.
    Detects //trigger strings and expands them into personalized multi-line text.
    """

    def __init__(self, custom_snippets: Optional[Dict[str, str]] = None):
        self.snippets: Dict[str, str] = {
            "//meet": "Let's schedule a quick 15-minute sync. Please find a time on my calendar: https://calendar.app.google/sync",
            "//email": "alex.morgan@company.com",
            "//thanks": "Thank you for the quick turnaround. I look forward to working together on this.",
            "//followup": "Hi team,\nFollowing up on our discussion yesterday. Please find the action items and next steps outlined below.",
            "//today": "{date}",
            "//zoom": "Join Zoom Meeting: https://zoom.us/j/1234567890 (Passcode: 102030)",
            "//intro": "Hi there,\nMy name is Alex, and I lead the on-device AI engineering team. Pleased to connect with you.",
            "//shrug": "¯\\_(ツ)_/¯",
        }

        if custom_snippets:
            self.snippets.update(custom_snippets)

    def is_trigger(self, word: str) -> bool:
        """Checks if word starts with the expansion prefix '//'."""
        clean = word.strip()
        return clean.startswith("//") and len(clean) > 2

    def expand(self, trigger_word: str) -> Optional[str]:
        """
        Expands a trigger word (e.g. '//meet') into its resolved text.
        Substitutes dynamic variables like {date}, {time}.
        """
        clean = trigger_word.strip().lower()
        if clean not in self.snippets:
            return None

        template = self.snippets[clean]

        # Resolve dynamic variables
        now = datetime.datetime.now()
        resolved = template.replace("{date}", now.strftime("%B %d, %Y"))
        resolved = resolved.replace("{time}", now.strftime("%I:%M %p"))

        return resolved

    def add_snippet(self, trigger: str, expansion: str) -> None:
        """Adds or updates a custom snippet."""
        clean_trigger = trigger.strip().lower()
        if not clean_trigger.startswith("//"):
            clean_trigger = f"//{clean_trigger}"
        self.snippets[clean_trigger] = expansion

    def remove_snippet(self, trigger: str) -> bool:
        """Removes a custom snippet."""
        clean_trigger = trigger.strip().lower()
        if clean_trigger in self.snippets:
            del self.snippets[clean_trigger]
            return True
        return False

    def get_all_snippets(self) -> Dict[str, str]:
        """Returns all configured snippets."""
        return dict(self.snippets)
