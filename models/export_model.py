"""
Model Exporter and INT8 Quantizer for Lightweight On-Device Autocorrect.
Downloads google/bert_uncased_L-2_H-128_A-2 (4.4M params), exports to ONNX
with dynamic shapes, and applies dynamic INT8 quantization for ultra-fast NPU/CPU execution.
"""

import os
import sys

# Force UTF-8 encoding on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import torch
from transformers import BertForMaskedLM, BertTokenizer
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType


def export_and_quantize():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_name = "google/bert_uncased_L-4_H-256_A-4"
    onnx_fp32_path = os.path.join(base_dir, "corrector_model_fp32.onnx")
    onnx_int8_path = os.path.join(base_dir, "corrector_model_quant.onnx")
    tokenizer_dir = os.path.join(base_dir, "tokenizer")

    os.makedirs(tokenizer_dir, exist_ok=True)
    print(f"Loading pretrained model: {model_name}...")
    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertForMaskedLM.from_pretrained(model_name)
    model.eval()

    # Save tokenizer locally so runtime is fully offline
    tokenizer.save_pretrained(tokenizer_dir)
    print(f"Tokenizer saved to {tokenizer_dir}")

    # Create dummy input with dynamic sequence length
    dummy_text = "I went to the [MASK] yesterday."
    inputs = tokenizer(dummy_text, return_tensors="pt")
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    print("Exporting model to ONNX FP32...")
    torch.onnx.export(
        model,
        (input_ids, attention_mask),
        onnx_fp32_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "logits": {0: "batch_size", 1: "sequence_length"},
        },
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )

    # Verify ONNX model
    onnx_model = onnx.load(onnx_fp32_path)
    onnx.checker.check_model(onnx_model)
    fp32_size_mb = os.path.getsize(onnx_fp32_path) / (1024 * 1024)
    print(f"ONNX FP32 model verified. Size: {fp32_size_mb:.2f} MB")

    # Quantize to INT8
    print("Applying dynamic INT8 quantization for NPU/CPU...")
    quantize_dynamic(
        model_input=onnx_fp32_path,
        model_output=onnx_int8_path,
        weight_type=QuantType.QInt8,
    )

    int8_size_mb = os.path.getsize(onnx_int8_path) / (1024 * 1024)
    print(f"INT8 Quantized Model saved to {onnx_int8_path}")
    print(f"Quantized Model Size: {int8_size_mb:.2f} MB (Compression: {fp32_size_mb / int8_size_mb:.1f}x)")

    # Clean up FP32 model to save disk space
    if os.path.exists(onnx_fp32_path):
        os.remove(onnx_fp32_path)

    print("Model export and quantization complete!")


if __name__ == "__main__":
    export_and_quantize()
