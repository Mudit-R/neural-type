# Neural-Type: Compliance-Grade Typing Infrastructure for Regulated Enterprises

**Neural-Type** is an ultra-low-latency, 100% on-device typing and contextual correction engine designed for regulated enterprise environments. Engineered to run entirely offline on local hardware—leveraging DirectML (NPU/GPU) and optimized CPU silicon—it guarantees **zero outbound network egress** so sensitive corporate communications, client data, and clinical notes never leave the physical endpoint.

---

## Zero-Egress Value Proposition

Traditional cloud-based AI writing assistants send raw keystrokes and document contents to remote servers, introducing severe data exfiltration liabilities, regulatory non-compliance, and breach of confidentiality.

**Neural-Type eliminates this risk by design:**
- **100% Air-Gapped Operation**: No API keys, no telemetry reporting, and zero external socket calls.
- **Microsecond In-Memory Execution**: Evaluates words and rolling 20-word semantic context locally using an INT8-quantized 8.13 MB neural ONNX model.
- **Local Compliance Audit Trails**: Generates structured, tamper-evident audit logs (JSONL) recording timestamps, event types, character deltas, and zero-egress proofs without ever logging raw user text.
- **Built-In PII & Secret Redactor**: Detects API keys, database credentials, SSNs, and credit cards directly on keystroke commit.

---

## Target Regulated Verticals

Neural-Type is purpose-built for industries where confidentiality is mandated by federal statute or fiduciary duty:

### 1. Legal & Professional Services
- **Protects Attorney-Client Privilege**: Guarantees work product, client depositions, and privileged communications are never ingested by third-party model trainers.
- **Fiduciary Secrecy**: Protects deal terms, litigation strategies, and merger drafts directly at the typing layer.

### 2. Healthcare & Life Sciences
- **Clinical Documentation Security**: Doctors and clinicians typing electronic health record (EHR) entries and clinical notes remain entirely on local hardware.
- **PHI Containment**: Prevents accidental leakage of patient identifiers into cloud writing platforms.

### 3. Financial Services & Capital Markets
- **Trading & Advisory Privacy**: Wealth managers, investment bankers, and trading desks can draft communications without exposing non-public material information (MNPI).
- **Credential & Account Guard**: Blocks accidental transmission of account numbers and database strings.

### 4. Defense & Government Contractors
- **Classified & CUI Workstations**: Designed for SCIFs, air-gapped terminals, and workstations handling Controlled Unclassified Information (CUI).
- **Supply Chain Integrity**: Standalone, auditable codebase with zero remote microservice dependencies.

---

## Compliance & Audit Framework Support

Neural-Type is architected to support enterprise compliance teams in meeting stringent regulatory standards. *(Note: Neural-Type provides technical controls designed to support compliance; institutional certification depends on organizational environment implementation).*

| Regulatory Framework | How Neural-Type Supports Compliance |
| :--- | :--- |
| **HIPAA** (Health Insurance Portability and Accountability Act) | Operates entirely on-device; Protected Health Information (PHI) is never transmitted over external networks or stored in third-party clouds. |
| **SOC 2 Type II** (Privacy & Confidentiality Criteria) | Enforces strict endpoint isolation; no user keystrokes or document fragments exit the boundary of the authorized workstation. |
| **FedRAMP-Adjacent & NIST SP 800-171** | Supports air-gapped and CUI computing environments by requiring zero internet connectivity or SaaS endpoints. |
| **Attorney-Client Privilege / ABA Model Rules** | Eliminates third-party disclosure waiver risks inherent in multi-tenant cloud-hosted LLM assistants. |
| **PCI-DSS & GLBA** | Integrated on-device regex scanning flags and masks cardholder numbers and financial account tokens before commit. |

---

## Core Technical Capabilities

- **Sub-2ms Inference Latency**: Runs 100% locally with zero cloud dependencies using an INT8 dynamic quantized neural ONNX model (8.13 MB footprint).
- **20-Word Context Window**: Evaluates the full preceding sentence context to resolve complex grammatical typos and real-word semantic confusions ("went to the parck" -> "park", "I will meat you" -> "meet", "a pare of shoes" -> "pair").
- **Hardware-Enforced Network Isolation**: Built-in socket-level verification confirms zero outbound network calls during all engine operations.
- **Auditable Metadata Trail**: Local JSONL compliance log records event timestamps, character volume, confidence scores, and rotation policies without logging sensitive user text.
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
├── audit_logs/                    # Local, structured JSONL compliance audit logs (rotates automatically)
├── models/
│   ├── export_model.py            # Model exporter & INT8 dynamic quantizer
│   ├── corrector_model_quant.onnx # Quantized 8.13MB neural model
│   └── tokenizer/                 # Offline WordPiece tokenizer
├── engine/
│   ├── audit_log.py               # Local compliance audit logger & 90-day retention engine
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
│   ├── test_network_isolation.py  # Socket-blocking network isolation proof test
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

Run the full suite including functional, stress, and network isolation tests:

```bash
.venv\Scripts\python -m pytest tests/ -v
```

To run the compliance network isolation proof specifically:

```bash
.venv\Scripts\python -m pytest tests/test_network_isolation.py -v
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
