# 🚀 AI-Powered Local Live Autocorrect (NPU & CPU Accelerated)

An on-device, low-latency, contextual autocorrect engine for Windows designed to run on modern **Intel** and **AMD** processors with **NPU** and multi-core CPU acceleration.

---

## ✨ Features

- **⚡ Sub-10ms Inference**: Runs on-device with zero cloud dependencies using an **INT8 Quantized Transformer Model** (`models/corrector_model_quant.onnx`, ~8.1 MB).
- **🧠 Contextual Understanding**: Takes the surrounding 10 words into context to fix grammatical typos and homophones (*"went to the parck"* $\to$ *"park"*, *"pare of shoes"* $\to$ *"pair"*).
- **↩️ Instant Tab Revert**: Hit `Tab` immediately after any correction to restore your original typed text.
- **🛡️ 100% Isolated & Safe**: Tested inside an isolated Python virtual environment (`.venv`) and a safe desktop sandbox UI before touching system hooks.
- **💻 Hardware Acceleration**: Automatic hardware detection supporting **Intel AI Boost (NPU)**, **AMD Ryzen AI (NPU)**, **DirectML GPU**, and **CPU AVX2/AVX-512**.

---

## 📁 Project Structure

```
AI powered autocorrect/
├── .venv/                         # Isolated Virtual Environment
├── models/
│   ├── export_model.py            # Model exporter & INT8 quantizer
│   ├── corrector_model_quant.onnx # Quantized 8.1MB neural model
│   └── tokenizer/                 # Offline WordPiece tokenizer
├── engine/
│   ├── context_buffer.py          # Rolling 10-word context ring buffer
│   ├── candidate_generator.py     # SymSpell dictionary & phonetic candidate generator
│   ├── onnx_infer.py              # DirectML / CPU ONNX inference engine
│   ├── undo_manager.py            # Tab-to-revert state machine
│   └── autocorrect_service.py     # Orchestrator & Bayesian scoring
├── test_sandbox/
│   └── sandbox_gui.py             # Modern Desktop Testbed UI with live telemetry
├── win32_hook/
│   └── global_keyboard_hook.py    # Optional global Windows keyboard hook
├── tests/
│   └── test_engine.py             # Automated unit & integration tests
├── run_sandbox.py                 # Sandbox launcher
└── requirements.txt               # Locked dependencies
```

---

## 🎮 How to Test in the Safe Sandbox (Recommended)

To launch the safe testbed desktop window:

```bash
.venv\Scripts\python run_sandbox.py
```

### What to try in the Sandbox:
1. **Type test phrases with intentional typos**:
   * Type `"I went to the parck tomorrow"` $\to$ watch `"parck"` automatically correct to `"park"` upon hitting Space.
   * Type `"I bought a pare of shoes"` $\to$ watch `"pare"` correct to `"pair"`.
   * Type `"dont"` $\to$ watch it correct to `"don't"`.
2. **Test Tab Revert**:
   * Immediately after a word is corrected, press **`Tab`** $\to$ the original typo is restored instantly!
3. **Check Real-Time Telemetry**:
   * Observe the active hardware engine, inference latency (e.g. `2.5 ms`), and confidence scores on the bottom status bar.

---

## 🌐 Optional: Global Windows Autocorrect Hook

When you are ready to test system-wide autocorrect across all Windows apps (Notepad, Chrome, Word, etc.):

```bash
.venv\Scripts\python win32_hook\global_keyboard_hook.py
```

### Safety Controls:
* **Toggle ON / OFF anytime**: Press `Ctrl + Alt + A`
* **Emergency Kill-Switch**: Press `Ctrl + Alt + Q` or `Ctrl + C` in the console
* **Revert Last Word**: Press `Tab`

---

## 🧪 Running Automated Tests

```bash
.venv\Scripts\python -m pytest tests/test_engine.py -v
```
