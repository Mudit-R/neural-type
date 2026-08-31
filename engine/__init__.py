"""
AI-Powered On-Device Smart Keyboard & Typing Assistant OS Engine.
"""

from .context_buffer import ContextBuffer
from .candidate_generator import CandidateGenerator
from .onnx_infer import OnnxInferenceEngine
from .undo_manager import UndoManager
from .text_expander import TextExpander
from .tone_transformer import ToneTransformer
from .privacy_guard import PrivacyGuard
from .autocorrect_service import AutocorrectService, CorrectionResult

__all__ = [
    "ContextBuffer",
    "CandidateGenerator",
    "OnnxInferenceEngine",
    "UndoManager",
    "TextExpander",
    "ToneTransformer",
    "PrivacyGuard",
    "AutocorrectService",
    "CorrectionResult",
]
