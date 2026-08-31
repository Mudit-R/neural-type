"""
Local Air-Gapped Tone Transformer & Grammar Polisher.
Transforms drafts into Executive Professional, Casual/Direct, and Concise Bullet formats offline.
"""

import re
from typing import List


class ToneTransformer:
    """
    On-device style and tone morphing engine.
    Transforms raw user text into polished business or casual formats without cloud APIs.
    """

    def __init__(self):
        self.professional_replacements = [
            (r"\basap\b", "at your earliest convenience"),
            (r"\bgonna\b", "going to"),
            (r"\bwanna\b", "would like to"),
            (r"\bgotta\b", "need to"),
            (r"\bhey\b", "Hello,"),
            (r"\bthx\b", "Thank you"),
            (r"\bthanks a lot\b", "Thank you very much"),
            (r"\blet me know\b", "Please keep me updated at your convenience"),
            (r"\bsorry for the delay\b", "Thank you for your patience"),
            (r"\bsorry for late reply\b", "Thank you for your patience"),
            (r"\btalk soon\b", "I look forward to speaking with you soon"),
            (r"\bbtw\b", "incidentally"),
            (r"\bi think that\b", "in my assessment,"),
            (r"\bno problem\b", "you are very welcome"),
            (r"\bcan you please fix this\b", "kindly review and advise on resolution"),
        ]

        self.casual_replacements = [
            (r"\bat your earliest convenience\b", "whenever you can"),
            (r"\bwould like to\b", "want to"),
            (r"\bgoing to\b", "gonna"),
            (r"\bkindly advise\b", "let me know"),
            (r"\bthank you for your patience\b", "thanks for waiting"),
            (r"\bplease find attached\b", "here is the"),
            (r"\bincidentally\b", "btw"),
        ]

    def to_professional(self, text: str) -> str:
        """Transforms colloquial drafts into polished executive communication."""
        if not text:
            return ""

        result = text.strip()
        for pattern, repl in self.professional_replacements:
            result = re.sub(pattern, repl, result, flags=re.IGNORECASE)

        # Capitalize sentences
        sentences = re.split(r"([.!?]\s+)", result)
        capitalized = []
        for s in sentences:
            if s and s[0].isalpha():
                capitalized.append(s[0].upper() + s[1:])
            else:
                capitalized.append(s)
        result = "".join(capitalized)

        if result and not result.endswith((".", "!", "?")):
            result += "."

        return result

    def to_casual(self, text: str) -> str:
        """Transforms formal text into friendly, direct communication."""
        if not text:
            return ""

        result = text.strip()
        for pattern, repl in self.casual_replacements:
            result = re.sub(pattern, repl, result, flags=re.IGNORECASE)

        return result

    def to_concise(self, text: str) -> str:
        """Condenses paragraphs into crisp bullet items."""
        if not text:
            return ""

        # Split into sentences
        sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if s.strip()]
        if not sentences:
            return text

        bullets = [f"- {s[0].upper() + s[1:] if s else s}" for s in sentences]
        return "\n".join(bullets)
