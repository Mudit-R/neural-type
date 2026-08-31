# On-Device AI Smart Keyboard OS

An ultra-low-latency, on-device contextual autocorrect and intelligent typing assistant for Windows. Engineered for modern Intel and AMD processors with NPU (Neural Processing Unit) and multi-core CPU acceleration.

---

## Core Capabilities

- **Sub-2ms Inference Latency**: Runs 100% locally with zero cloud dependencies using an INT8 quantized dynamic ONNX model (8.13 MB footprint).
- **20-Word Context Window**: Evaluates the full preceding sentence context to resolve complex grammatical typos and real-word semantic confusions ("went to the parck" -> "park", "I will meat you" -> "meet", "a pare of shoes" -> "pair").
- **Next-Word Predictive Ghost Text**: Generates real-time sentence completions ahead of the cursor. Press Tab or Right Arrow to autocomplete thoughts instantly.
- **Smart Text Expander**: Instant expansion of `//` shortcuts (`//meet`, `//email`, `//today`, `//followup`) into multi-line templates.
- **Air-Gapped Tone Transformer**: Offline single-click rewriting into Executive Professional, Casual Direct, and Concise Bullet formats.
- **Enterprise Privacy & PII Guard**: Scans text in real time for API keys, credit cards, SSNs, and private credentials, with one-click local redaction.
- **Instant Hardware-State Tab Revert**: Press Tab immediately after any correction to restore the original typed text within 3.5 seconds.
- **Hardware Acceleration**: Automatic runtime detection supporting DirectML (Intel AI Boost NPU, AMD Ryzen AI NPU, integrated/discrete GPUs) and CPU AVX2/AVX-512.

---

## Project Structure

```
AI powered autocorrect/
├── .venv/                         # Isolated Virtual Environment
├── models/
│   ├── export_model.py            # Model exporter & INT8 dynamic quantizer
│   ├── corrector_model_quant.onnx # Quantized 8.13MB neural model
│   └── tokenizer/                 # Offline WordPiece tokenizer
├── engine/
│   ├── context_buffer.py          # 20-word rolling ring buffer
│   ├── candidate_generator.py     # SymSpell dictionary & phonetic candidate generator
│   ├── onnx_infer.py              # DirectML / CPU ONNX inference & ghost prediction
│   ├── undo_manager.py            # Tab-to-revert state machine
│   ├── text_expander.py           # Sub-0.1ms snippet template expander
│   ├── tone_transformer.py        # Air-gapped offline tone morpher
│   ├── privacy_guard.py           # Enterprise PII and API key scanner
│   └── autocorrect_service.py     # Unified orchestrator & Bayesian scorer
├── test_sandbox/
│   └── sandbox_gui.py             # Desktop Tkinter GUI with live telemetry
├── win32_hook/
│   └── global_keyboard_hook.py    # Global Windows keyboard hook service
├── tests/
│   ├── test_engine.py             # Core engine unit tests
│   ├── test_smart_keyboard_features.py # Ghost text, expander, tone, privacy tests
│   └── test_stress_benchmarks.py  # 250-word burst & latency stress suite
├── web_app.py                     # Local web sandbox server (http://localhost:8000)
├── benchmark_investor_report.py   # Comprehensive accuracy & latency audit report
├── demo.py                        # Terminal interactive demo simulator
├── interactive_cli.py             # CLI live typing runner
├── run_sandbox.py                 # Desktop launcher
└── requirements.txt               # Locked dependencies
```

---

## Quick Start: Testing the Platform

### Method 1: Web Sandbox (Recommended)

Run the local web sandbox server:

```bash
.venv\Scripts\python web_app.py
```

Open your browser to: `http://localhost:8000`

#### Scenarios to Test:
1. **Contextual Autocorrect**: Type `"I went to the parck "` -> automatically corrects to `"park"`.
2. **Real-Word Semantic Errors**: Type `"I will meat you at the cafe "` -> automatically corrects to `"meet"`.
3. **Tab Revert**: Press `Tab` immediately after any correction -> restores original typo.
4. **Predictive Ghost Text**: Type `"I want to go to the"` -> observe ghost suggestion -> press `Right Arrow` to accept.
5. **Text Expander**: Type `"//meet "` -> expands into full meeting sync invite.
6. **Tone Transformer**: Enter text and click "Make Professional" or "Make Concise".
7. **Privacy Guard**: Paste a dummy key (`sk-1234567890abcdef1234567890abcdef`) -> observe instant privacy detection.

---

### Method 2: Native Desktop Window

Launch the standalone desktop interface:

```bash
.venv\Scripts\python run_sandbox.py
```
*(Or double-click `launch_sandbox.bat` in File Explorer)*

---

### Method 3: Terminal Simulation

Run the automated keystroke simulation:

```bash
.venv\Scripts\python demo.py
```

---

## Benchmark Audit & Accuracy Report

Run the complete investor-grade accuracy and throughput audit:

```bash
.venv\Scripts\python benchmark_investor_report.py
```

### Measured Performance Summary:
- **Typo & Phonetic Top-1 Accuracy**: 96.7%
- **Real-Word Semantic Disambiguation Accuracy**: 94.4%
- **Clean Text Preservation (Precision)**: 100.0%
- **False Positive Rate**: 0.00%
- **P50 Latency**: 0.05 ms
- **P95 Latency**: 1.14 ms
- **P99 Latency**: 1.36 ms
- **Throughput Capacity**: 135,000+ Words/Minute
- **RAM Footprint**: ~47.5 MB total process memory

---

## Running the Automated Test Suite

```bash
.venv\Scripts\python -m pytest tests/ -v
```

---

## System-Wide Global Hook (Optional)

To enable global system-wide autocorrect across all Windows applications (Word, Chrome, Slack, Notepad, etc.):

```bash
.venv\Scripts\python win32_hook\global_keyboard_hook.py
```

### Shortcuts:
- **Toggle Active / Paused**: `Ctrl + Alt + A`
- **Emergency Kill-Switch**: `Ctrl + Alt + Q`
- **Undo Correction**: `Tab`
