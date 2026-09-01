"""
ONNX Runtime Inference Engine for Contextual Word Scoring & Next-Word Prediction.
Supports DirectML (Intel AI Boost / AMD Ryzen AI NPU / GPU) and CPU (AVX2/AVX-512).
"""

import os
import sys
import time
import math
import numpy as np
import onnxruntime as ort
from transformers import BertTokenizer
from typing import List, Tuple, Dict, Any, Optional


class OnnxInferenceEngine:
    """
    Sub-10ms Contextual Neural Scorer & Predictive Ghost Text Generator
    using INT8 Quantized ONNX Model with Bayesian Noisy-Channel scoring.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        tokenizer_dir: Optional[str] = None,
    ):
        if getattr(sys, "frozen", False):
            candidates = [
                getattr(sys, "_MEIPASS", ""),
                os.path.join(getattr(sys, "_MEIPASS", ""), "_internal"),
                os.path.dirname(sys.executable),
                os.path.join(os.path.dirname(sys.executable), "_internal"),
            ]
            base_dir = next(
                (c for c in candidates if c and os.path.exists(os.path.join(c, "models", "corrector_model_quant.onnx"))),
                candidates[0],
            )
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        if model_path is None:
            model_path = os.path.join(base_dir, "models", "corrector_model_quant.onnx")
        if tokenizer_dir is None:
            tokenizer_dir = os.path.join(base_dir, "models", "tokenizer")

        self.model_path = model_path
        self.tokenizer_dir = tokenizer_dir

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Quantized ONNX model not found at {model_path}")

        # Load offline tokenizer
        self.tokenizer = BertTokenizer.from_pretrained(tokenizer_dir)
        self.mask_token_id = self.tokenizer.mask_token_id  # 103 for BERT
        self.mask_token = self.tokenizer.mask_token        # "[MASK]"

        # Configure ONNX Runtime Session Options
        self.sess_options = ort.SessionOptions()
        self.sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.sess_options.intra_op_num_threads = 2
        self.sess_options.inter_op_num_threads = 1

        # Execution Providers Priority: DirectML (NPU/GPU) -> CPU
        available_providers = ort.get_available_providers()
        desired_providers = []
        if "DmlExecutionProvider" in available_providers:
            desired_providers.append("DmlExecutionProvider")
        if "OpenVINOExecutionProvider" in available_providers:
            desired_providers.append("OpenVINOExecutionProvider")
        desired_providers.append("CPUExecutionProvider")

        print(f"[OnnxInferenceEngine] Initializing with providers: {desired_providers}")
        self.session = ort.InferenceSession(
            model_path,
            sess_options=self.sess_options,
            providers=desired_providers,
        )

        self.active_provider = self.session.get_providers()[0]
        print(f"[OnnxInferenceEngine] Active Execution Provider: {self.active_provider}")

        # Warm-up forward pass
        self._warmup()

    def _warmup(self) -> None:
        """Executes a single dummy inference to pre-allocate caches."""
        dummy_text = "I went to the [MASK] yesterday."
        inputs = self.tokenizer(dummy_text, return_tensors="np")
        feed = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64),
        }
        self.session.run(["logits"], feed)

    def score_candidates(
        self,
        context_prefix: str,
        candidates: List[Tuple[str, int, int]],  # (word, frequency, edit_distance)
        context_suffix: str = "",
    ) -> Tuple[List[Tuple[str, float]], float]:
        """
        Computes contextual probability for each candidate using Bayesian Noisy Channel scoring.
        Returns: ([(candidate_word, probability), ...], latency_ms)
        """
        if not candidates:
            return [], 0.0

        t0 = time.perf_counter()

        # Build masked sentence: "context_prefix [MASK] context_suffix"
        prefix = context_prefix.strip()
        suffix = context_suffix.strip()

        if prefix and suffix:
            sentence = f"{prefix} {self.mask_token} {suffix}"
        elif prefix:
            sentence = f"{prefix} {self.mask_token}"
        else:
            sentence = f"{self.mask_token} {suffix}" if suffix else self.mask_token

        encoded = self.tokenizer(
            sentence,
            return_tensors="np",
            truncation=True,
            max_length=128,
        )

        input_ids = encoded["input_ids"].astype(np.int64)
        attention_mask = encoded["attention_mask"].astype(np.int64)

        # Locate [MASK] token position
        mask_positions = np.where(input_ids[0] == self.mask_token_id)[0]
        if len(mask_positions) == 0:
            mask_idx = len(input_ids[0]) - 2
        else:
            mask_idx = mask_positions[0]

        # Run ONNX inference
        feed = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }
        outputs = self.session.run(["logits"], feed)
        logits = outputs[0]

        mask_logits = logits[0, mask_idx, :]

        # Extract logits and apply Bayesian prior weighting
        candidate_composite_scores = []
        for cand_tuple in candidates:
            if isinstance(cand_tuple, (list, tuple)):
                cand_word = cand_tuple[0]
                freq = cand_tuple[1] if len(cand_tuple) > 1 else 1000
                dist = cand_tuple[2] if len(cand_tuple) > 2 else 0
            else:
                cand_word = str(cand_tuple)
                freq = 1000
                dist = 0

            cand_tokens = self.tokenizer.encode(cand_word.lower(), add_special_tokens=False)
            if cand_tokens:
                cand_id = cand_tokens[0]
                neural_logit = float(mask_logits[cand_id]) if cand_id < len(mask_logits) else -50.0
            else:
                neural_logit = -50.0

            freq_prior = math.log(max(1, freq) + 1.0)
            composite_score = neural_logit + 0.85 * freq_prior - 2.0 * dist
            candidate_composite_scores.append((cand_word, composite_score))

        # Softmax over candidate pool
        words = [item[0] for item in candidate_composite_scores]
        scores_arr = np.array([item[1] for item in candidate_composite_scores], dtype=np.float64)
        exp_scores = np.exp(scores_arr - np.max(scores_arr))
        probs = exp_scores / (np.sum(exp_scores) + 1e-12)

        results = [(w, float(p)) for w, p in zip(words, probs)]
        results.sort(key=lambda item: item[1], reverse=True)

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return results, latency_ms

    def predict_next_word(self, context_prefix: str, top_k: int = 3) -> Tuple[List[str], float]:
        """
        Predicts the top next-word continuations (Ghost Text) given the preceding context.
        Returns: (['predicted_word1', 'predicted_word2', ...], latency_ms)
        """
        prefix = context_prefix.strip()
        if not prefix:
            return [], 0.0

        t0 = time.perf_counter()
        sentence = f"{prefix} {self.mask_token}"

        encoded = self.tokenizer(
            sentence,
            return_tensors="np",
            truncation=True,
            max_length=128,
        )

        input_ids = encoded["input_ids"].astype(np.int64)
        attention_mask = encoded["attention_mask"].astype(np.int64)

        mask_positions = np.where(input_ids[0] == self.mask_token_id)[0]
        mask_idx = mask_positions[0] if len(mask_positions) > 0 else (len(input_ids[0]) - 2)

        feed = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }
        outputs = self.session.run(["logits"], feed)
        logits = outputs[0][0, mask_idx, :]

        # Get top-30 token indices to filter subwords and punctuation
        top_indices = np.argsort(logits)[::-1][:35]

        predictions = []
        for idx in top_indices:
            token_str = self.tokenizer.decode([idx]).strip()
            if not token_str or token_str.startswith("##") or token_str.startswith("["):
                continue
            if len(token_str) <= 1 and not token_str.isalnum():
                continue
            if token_str.lower() not in [p.lower() for p in predictions]:
                predictions.append(token_str)
            if len(predictions) >= top_k:
                break

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return predictions, latency_ms

    def get_hardware_info(self) -> Dict[str, Any]:
        """Returns diagnostic info about active accelerator."""
        return {
            "active_provider": self.active_provider,
            "all_providers": self.session.get_providers(),
            "model_size_mb": os.path.getsize(self.model_path) / (1024 * 1024),
            "is_npu_or_gpu": "Dml" in self.active_provider or "OpenVINO" in self.active_provider,
        }
