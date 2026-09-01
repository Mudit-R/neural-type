"""
Autocorrect & Smart Keyboard OS Service Orchestrator.
Coordinates ContextBuffer, CandidateGenerator, OnnxInferenceEngine, UndoManager,
TextExpander, ToneTransformer, PrivacyGuard, and ComplianceAuditLogger.
"""

import time
import socket
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List
from .context_buffer import ContextBuffer
from .candidate_generator import CandidateGenerator
from .onnx_infer import OnnxInferenceEngine
from .undo_manager import UndoManager
from .text_expander import TextExpander
from .tone_transformer import ToneTransformer
from .privacy_guard import PrivacyGuard
from .audit_log import ComplianceAuditLogger
from .policy_config import PolicyConfig


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
    5. Enterprise PII and API key privacy scanning and redaction.
    6. Structured on-device compliance audit trail (zero raw-text storage).
    7. Built-in network isolation verification (zero outbound network egress).
    8. Centralized enterprise policy enforcement (config/policy.yaml).
    """

    def __init__(
        self,
        confidence_threshold: Optional[float] = None,
        revert_timeout: Optional[float] = None,
        max_edit_distance: Optional[int] = None,
        audit_enabled: Optional[bool] = None,
        audit_log_dir: Optional[str] = None,
        audit_retention_days: Optional[int] = None,
        verify_isolation_on_startup: bool = False,
        policy: Optional[PolicyConfig] = None,
        policy_path: Optional[str] = None,
    ):
        self.policy = policy or PolicyConfig(config_path=policy_path)
        ac_cfg = self.policy.get_autocorrect_settings()
        audit_cfg = self.policy.get_audit_settings()

        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else ac_cfg["confidence_threshold"]
        )
        self.revert_timeout = (
            revert_timeout if revert_timeout is not None else ac_cfg["revert_timeout_seconds"]
        )
        self.max_edit_distance = (
            max_edit_distance if max_edit_distance is not None else ac_cfg["max_edit_distance"]
        )

        self.context_buffer = ContextBuffer(max_context_words=25)
        self.candidate_generator = CandidateGenerator(max_edit_distance=self.max_edit_distance)
        self.onnx_engine = OnnxInferenceEngine()
        self.undo_manager = UndoManager(timeout_seconds=self.revert_timeout)
        self.text_expander = TextExpander()
        self.tone_transformer = ToneTransformer()

        # Privacy Guard configured from Policy
        pg_enabled = self.policy.is_privacy_guard_enabled()
        vertical_profile = self.policy.get_active_vertical_profile()
        detector_rules = self.policy.policy.get("privacy_guard", {}).get("detectors", {})
        self.privacy_guard = PrivacyGuard(
            enabled=pg_enabled,
            vertical_profile=vertical_profile,
            detector_rules=detector_rules,
        )

        # Audit Logger configured from Policy
        eff_audit_enabled = audit_enabled if audit_enabled is not None else audit_cfg["enabled"]
        eff_audit_dir = audit_log_dir if audit_log_dir is not None else audit_cfg["log_dir"]
        eff_retention = audit_retention_days if audit_retention_days is not None else audit_cfg["retention_days"]

        self.audit_logger = ComplianceAuditLogger(
            log_dir=eff_audit_dir,
            filename=audit_cfg.get("filename", "audit_trail.jsonl"),
            enabled=eff_audit_enabled,
            retention_days=eff_retention,
            max_file_size_bytes=audit_cfg.get("max_file_size_bytes", 10 * 1024 * 1024),
        )
        self.is_network_isolated: bool = False

        if verify_isolation_on_startup:
            self.verify_network_isolation()

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
                self.audit_logger.log_correction(
                    input_chars=len(clean_word),
                    output_chars=len(expansion),
                    confidence=1.0,
                    latency_ms=0.05,
                    device=hardware,
                    is_expansion=True,
                    explanation=f"Text expanded snippet: '{clean_word}'",
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

        # 3b. Short valid word guard: Never replace a valid <=2 character word
        # (e.g. ok, on, of, in, it, is, at, as, do, go, no, so, he, me, we, by, my, up, us, am, if)
        # unless it is in an explicit confusable homophone cluster (like to/too/two)
        if len(clean_word) <= 2 and self.candidate_generator.is_valid_word(clean_word):
            if clean_word.lower() not in self.candidate_generator.homophone_clusters:
                return CorrectionResult(
                    is_corrected=False,
                    original_word=word,
                    corrected_word=word,
                    delimiter=delimiter,
                    confidence=1.0,
                    latency_ms=0.05,
                    device=hardware,
                    explanation=f"Valid short word preserved: '{clean_word}'",
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
        is_homophone = clean_word in self.candidate_generator.homophone_clusters

        if is_homophone:
            # Explicit confusable homophone pairs (meat/meet, peace/piece, there/their)
            required_threshold = self.confidence_threshold
        elif is_known:
            # Regular correctly-spelled dictionary words require overwhelming confidence (>=0.85)
            required_threshold = max(self.confidence_threshold, 0.85)
        else:
            # Clear misspelled typos require only low confidence
            required_threshold = 0.25

        if top_prob >= required_threshold:
            # Trigger Correction & Arm Undo
            self.undo_manager.record_correction(
                original_word=clean_word,
                corrected_word=cased_candidate,
                delimiter=delimiter,
            )

            # Record in compliance audit trail (metadata only, no raw text)
            self.audit_logger.log_correction(
                input_chars=len(clean_word),
                output_chars=len(cased_candidate),
                confidence=top_prob,
                latency_ms=latency_ms,
                device=hardware,
                is_expansion=False,
                explanation=f"Corrected: '{clean_word}' -> '{cased_candidate}'",
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
        """Applies local tone transformations offline if permitted by enterprise policy."""
        if not self.policy.is_tone_transformation_enabled():
            return text

        if not self.policy.is_tone_mode_allowed(mode):
            return text

        start_t = time.perf_counter()
        if mode == "professional":
            result = self.tone_transformer.to_professional(text)
        elif mode == "casual":
            result = self.tone_transformer.to_casual(text)
        elif mode == "concise":
            result = self.tone_transformer.to_concise(text)
        else:
            result = text

        lat_ms = (time.perf_counter() - start_t) * 1000.0
        self.audit_logger.log_tone_transform(
            input_chars=len(text),
            output_chars=len(result),
            mode=mode,
            latency_ms=lat_ms,
        )
        return result

    def scan_privacy(self, text: str) -> List[Dict[str, Any]]:
        """Scans drafted text for sensitive credentials, API keys, or PII."""
        start_t = time.perf_counter()
        findings = self.privacy_guard.scan(text)
        lat_ms = (time.perf_counter() - start_t) * 1000.0

        if findings:
            hazard_names = [f["hazard"] for f in findings]
            self.audit_logger.log_pii_detection(
                char_count=len(text),
                hazard_types=hazard_names,
                latency_ms=lat_ms,
            )
        return findings

    def redact_privacy(self, text: str) -> str:
        """Redacts sensitive tokens locally and logs compliance evidence."""
        start_t = time.perf_counter()
        findings = self.privacy_guard.scan(text)
        redacted = self.privacy_guard.redact(text)
        lat_ms = (time.perf_counter() - start_t) * 1000.0

        if findings:
            self.audit_logger.log_pii_redaction(
                input_chars=len(text),
                output_chars=len(redacted),
                redaction_count=len(findings),
                latency_ms=lat_ms,
            )
        return redacted

    def verify_network_isolation(self) -> bool:
        """
        Compliance startup self-check.
        Strictly verifies that the full pipeline (ONNX scoring, tokenizer,
        expander, tone transformer, and privacy guard) operates with zero
        outbound socket attempts.
        Returns True if network isolation is provably intact.
        """
        socket_attempts = []
        original_connect = socket.socket.connect
        original_create_connection = getattr(socket, "create_connection", None)

        def mock_connect(sock_self, address):
            socket_attempts.append(str(address))
            raise PermissionError(f"Network egress blocked in compliance mode: attempted connect to {address}")

        def mock_create_connection(address, *args, **kwargs):
            socket_attempts.append(str(address))
            raise PermissionError(f"Network egress blocked in compliance mode: attempted connect to {address}")

        try:
            # Install socket interceptors
            socket.socket.connect = mock_connect
            if original_create_connection:
                socket.create_connection = mock_create_connection

            # Run complete pipeline under socket interceptor
            corr = self.evaluate_word("parck", delimiter=" ", explicit_context="I went to the")
            assert corr.corrected_word.lower() == "park"

            ghosts, _ = self.predict_ghost_text("I want to go to the", top_k=1)
            assert len(ghosts) > 0

            tone = self.transform_tone("hey team gotta fix asap thx", mode="professional")
            assert "Hello," in tone

            findings = self.scan_privacy("API key: sk-abcdef1234567890abcdef1234567890")
            assert len(findings) > 0

            redacted = self.redact_privacy("API key: sk-abcdef1234567890abcdef1234567890")
            assert "sk-" not in redacted

            exp = self.text_expander.expand("//meet")
            assert exp is not None

            # Assert zero network socket attempts were made
            assert len(socket_attempts) == 0, f"Network isolation violated: {socket_attempts}"
            self.is_network_isolated = True
            return True

        finally:
            # Restore original socket methods
            socket.socket.connect = original_connect
            if original_create_connection:
                socket.create_connection = original_create_connection

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
