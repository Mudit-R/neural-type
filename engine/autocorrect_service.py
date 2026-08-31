"""
Autocorrect & Smart Keyboard OS Service Orchestrator.
Coordinates ContextBuffer, CandidateGenerator, OnnxInferenceEngine, UndoManager,
TextExpander, ToneTransformer, and PrivacyGuard.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List
from .context_buffer import ContextBuffer
from .candidate_generator import CandidateGenerator
from .onnx_infer import OnnxInferenceEngine
from .undo_manager import UndoManager
from .text_expander import TextExpander
from .tone_transformer import ToneTransformer
from .privacy_guard import PrivacyGuard


@dataclass
class CorrectionResult:
    is_corrected: bool
    original_word: str
    corrected_word: str
    delimiter: str
    confidence: float
    latency_ms: float
    device: str
    explanation: str
    is_expansion: bool = False


class AutocorrectService:
    """
    Main live Smart Keyboard OS service supporting:
    1. 20-word rolling context autocorrect and semantic disambiguation.
    2. Instant snippet expansion for //triggers.
    3. Next-word predictive ghost text completion.
    4. Air-gapped tone transformation.
    5. Enterprise PII and API key privacy scanning.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.55,
        revert_timeout: float = 3.5,
        max_edit_distance: int = 2,
    ):
        self.confidence_threshold = confidence_threshold
        self.context_buffer = ContextBuffer(max_context_words=25)
        self.candidate_generator = CandidateGenerator(max_edit_distance=max_edit_distance)
        self.onnx_engine = OnnxInferenceEngine()
        self.undo_manager = UndoManager(timeout_seconds=revert_timeout)
        self.text_expander = TextExpander()
        self.tone_transformer = ToneTransformer()
        self.privacy_guard = PrivacyGuard()

    def evaluate_word(
        self, word: str, delimiter: str = " ", explicit_context: Optional[str] = None
    ) -> CorrectionResult:
        """
        Evaluates a finished word in the preceding 20-word context.
        Checks for text expansions, syntax guards, high-frequency lexicon, and neural ONNX scoring.
        """
        clean_word = word.strip()
        hardware = self.onnx_engine.active_provider

        # 1. Text Expander Fast-Path (e.g. //meet, //email, //today)
        if self.text_expander.is_trigger(clean_word):
            expansion = self.text_expander.expand(clean_word)
            if expansion:
                self.undo_manager.record_correction(
                    original_word=clean_word,
                    corrected_word=expansion,
                    delimiter=delimiter,
                )
                return CorrectionResult(
                    is_corrected=True,
                    original_word=clean_word,
                    corrected_word=expansion,
                    delimiter=delimiter,
                    confidence=1.0,
                    latency_ms=0.05,
                    device=hardware,
                    explanation=f"Text expanded snippet: '{clean_word}'",
                    is_expansion=True,
                )

        # 2. Syntax Guard (Skip code, numbers, URLs, acronyms)
        if self.candidate_generator.is_syntax_guarded(clean_word):
            return CorrectionResult(
                is_corrected=False,
                original_word=word,
                corrected_word=word,
                delimiter=delimiter,
                confidence=1.0,
                latency_ms=0.01,
                device=hardware,
                explanation="Syntax guarded (Code/Number/Acronym)",
            )

        # 3. Check if word is unambiguous high-frequency dictionary word
        if self.candidate_generator.is_valid_high_frequency_word(clean_word):
            return CorrectionResult(
                is_corrected=False,
                original_word=word,
                corrected_word=word,
                delimiter=delimiter,
                confidence=1.0,
                latency_ms=0.05,
                device=hardware,
                explanation="Valid high-frequency word (Bypassed AI)",
            )

        # 4. Retrieve candidates from fast SymSpell / Confusable Lexicon
        candidate_entries = self.candidate_generator.get_candidates(clean_word, max_candidates=6)
        if not candidate_entries:
            return CorrectionResult(
                is_corrected=False,
                original_word=word,
                corrected_word=word,
                delimiter=delimiter,
                confidence=0.0,
                latency_ms=0.1,
                device=hardware,
                explanation="No valid dictionary candidates found",
            )

        # 5. Neural Context Scoring via ONNX Runtime across up to 20 words
        context_str = (
            explicit_context
            if explicit_context is not None
            else self.context_buffer.get_context_string(count=20)
        )
        ranked_candidates, latency_ms = self.onnx_engine.score_candidates(
            context_prefix=context_str,
            candidates=candidate_entries,
        )

        if not ranked_candidates:
            return CorrectionResult(
                is_corrected=False,
                original_word=word,
                corrected_word=word,
                delimiter=delimiter,
                confidence=0.0,
                latency_ms=latency_ms,
                device=hardware,
                explanation="Model scoring returned no candidates",
            )

        top_candidate, top_prob = ranked_candidates[0]

        # 6. Apply original casing (e.g. Parck -> Park)
        cased_candidate = self.candidate_generator.apply_casing(clean_word, top_candidate)

        # 7. Confidence and Equivalence Check
        if cased_candidate.lower() == clean_word.lower():
            return CorrectionResult(
                is_corrected=False,
                original_word=word,
                corrected_word=word,
                delimiter=delimiter,
                confidence=top_prob,
                latency_ms=latency_ms,
                device=hardware,
                explanation="Original word confirmed by context",
            )

        is_known = self.candidate_generator.is_valid_word(clean_word)
        required_threshold = self.confidence_threshold if is_known else 0.25

        if top_prob >= required_threshold:
            # Trigger Correction & Arm Undo
            self.undo_manager.record_correction(
                original_word=clean_word,
                corrected_word=cased_candidate,
                delimiter=delimiter,
            )

            return CorrectionResult(
                is_corrected=True,
                original_word=clean_word,
                corrected_word=cased_candidate,
                delimiter=delimiter,
                confidence=top_prob,
                latency_ms=latency_ms,
                device=hardware,
                explanation=f"Corrected: '{clean_word}' -> '{cased_candidate}' (Conf: {top_prob:.1%})",
            )
        else:
            return CorrectionResult(
                is_corrected=False,
                original_word=word,
                corrected_word=word,
                delimiter=delimiter,
                confidence=top_prob,
                latency_ms=latency_ms,
                device=hardware,
                explanation=f"Below confidence threshold ({top_prob:.1%} < {required_threshold:.1%})",
            )

    def predict_ghost_text(self, context_prefix: str, top_k: int = 1) -> Tuple[List[str], float]:
        """Predicts the next word(s) in context for inline Ghost Text."""
        return self.onnx_engine.predict_next_word(context_prefix=context_prefix, top_k=top_k)

    def transform_tone(self, text: str, mode: str = "professional") -> str:
        """Applies local tone transformations offline."""
        if mode == "professional":
            return self.tone_transformer.to_professional(text)
        elif mode == "casual":
            return self.tone_transformer.to_casual(text)
        elif mode == "concise":
            return self.tone_transformer.to_concise(text)
        return text

    def scan_privacy(self, text: str) -> List[Dict[str, Any]]:
        """Scans drafted text for sensitive credentials, API keys, or PII."""
        return self.privacy_guard.scan(text)

    def handle_delimiter_commit(
        self, delimiter: str = " ", explicit_context: Optional[str] = None
    ) -> Tuple[str, CorrectionResult]:
        """
        Commits active in-flight word, evaluates it in preceding 20-word context,
        and pushes the final word into history.
        """
        raw_word = self.context_buffer.get_current_word()
        self.context_buffer.current_word_chars.clear()

        if not raw_word:
            return "", CorrectionResult(
                is_corrected=False,
                original_word="",
                corrected_word="",
                delimiter=delimiter,
                confidence=1.0,
                latency_ms=0.0,
                device=self.onnx_engine.active_provider,
                explanation="Empty buffer",
            )

        res = self.evaluate_word(raw_word, delimiter, explicit_context=explicit_context)
        final_word = res.corrected_word if res.is_corrected else raw_word
        self.context_buffer.history.append(final_word)

        return raw_word, res

    def handle_tab_revert(self) -> Optional[Tuple[str, str, str]]:
        """Consumes Tab revert if armed and restores original history word."""
        revert = self.undo_manager.consume_revert()
        if revert:
            corrected, original, delim = revert
            self.context_buffer.update_last_history_word(corrected, original)
            return revert
        return None

    def feed_character(self, char: str) -> None:
        """User typed a letter: append to current word and disarm undo."""
        self.context_buffer.push_char(char)
        self.undo_manager.invalidate()

    def feed_backspace(self) -> Optional[str]:
        """User pressed Backspace: remove last character."""
        return self.context_buffer.pop_char()

    def reset(self) -> None:
        """Resets all internal buffers and undo state."""
        self.context_buffer.clear()
        self.undo_manager.invalidate()
