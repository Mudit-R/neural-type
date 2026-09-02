"""
Local Web Sandbox Server for AI-Powered Smart Keyboard OS.
Serves a high-performance interactive web UI on http://localhost:8000
with 20-word context autocorrect, Ghost Text prediction, Text Expander,
Tone Transformer, and Enterprise Privacy Guard.
"""

import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.autocorrect_service import AutocorrectService

# Global service instance
service = AutocorrectService(confidence_threshold=0.95, revert_timeout=3.5)
hw_info = service.onnx_engine.get_hardware_info()

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>On-Device AI Smart Keyboard OS - Local Sandbox</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0a0c10;
            --card-bg: rgba(20, 23, 33, 0.85);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-purple: #8b5cf6;
            --accent-red: #ef4444;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: var(--bg);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(59, 130, 246, 0.12), transparent 45%),
                radial-gradient(circle at 85% 85%, rgba(139, 92, 246, 0.12), transparent 45%);
        }

        .container {
            width: 100%;
            max-width: 980px;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            backdrop-filter: blur(16px);
            box-shadow: 0 12px 36px rgba(0,0,0,0.4);
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .title-group h1 {
            font-size: 1.35rem;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .title-group p {
            color: var(--text-secondary);
            font-size: 0.82rem;
            margin-top: 0.2rem;
        }

        .badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 600;
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .badge-pill.cpu {
            background: rgba(59, 130, 246, 0.15);
            color: var(--accent-blue);
            border: 1px solid rgba(59, 130, 246, 0.3);
        }

        .editor-section {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .btn-group {
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
        }

        button {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 0.38rem 0.75rem;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        button:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.2);
        }

        button.primary {
            background: rgba(59, 130, 246, 0.2);
            color: #93c5fd;
            border-color: rgba(59, 130, 246, 0.4);
        }
        button.primary:hover {
            background: rgba(59, 130, 246, 0.3);
        }

        button.tone-btn {
            background: rgba(139, 92, 246, 0.15);
            color: #c4b5fd;
            border-color: rgba(139, 92, 246, 0.3);
        }
        button.tone-btn:hover {
            background: rgba(139, 92, 246, 0.25);
        }

        .editor-wrapper {
            position: relative;
            width: 100%;
        }

        textarea {
            width: 100%;
            height: 180px;
            background: #0f1118;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 1rem;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.05rem;
            line-height: 1.6;
            resize: vertical;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        textarea:focus {
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }

        .ghost-bar {
            background: rgba(15, 17, 24, 0.7);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 0.5rem 0.85rem;
            font-size: 0.82rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .ghost-preview {
            color: #60a5fa;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 500;
        }

        .revert-indicator {
            padding: 0.65rem 1rem;
            border-radius: 10px;
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.3);
            color: #fbbf24;
            font-size: 0.82rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            opacity: 0;
            transform: translateY(-4px);
            transition: all 0.25s ease;
        }

        .revert-indicator.show {
            opacity: 1;
            transform: translateY(0);
        }

        .privacy-alert {
            padding: 0.65rem 1rem;
            border-radius: 10px;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
            font-size: 0.82rem;
            display: none;
            align-items: center;
            justify-content: space-between;
        }

        .privacy-alert.show {
            display: flex;
        }

        .metrics-strip {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.75rem;
        }

        .metric-box {
            background: rgba(15, 17, 24, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 0.75rem 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }

        .metric-box .label {
            font-size: 0.72rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-box .val {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .metric-box .val.green { color: var(--accent-green); }
        .metric-box .val.blue { color: var(--accent-blue); }
        .metric-box .val.amber { color: var(--accent-amber); }

        .log-section h3 {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .log-container {
            background: #0f1118;
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 0.75rem;
            height: 120px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            display: flex;
            flex-direction: column-reverse;
            gap: 0.35rem;
        }

        .log-item {
            color: var(--text-secondary);
            padding: 0.15rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }
        .log-item .highlight {
            color: var(--accent-green);
            font-weight: 600;
        }
        .log-item .latency {
            color: #60a5fa;
            font-size: 0.75rem;
        }
        .log-item.reverted {
            color: var(--accent-amber);
        }

        kbd {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            padding: 0.1rem 0.35rem;
            font-size: 0.72rem;
            font-family: inherit;
        }
    </style>
</head>
<body>

<div class="container">
    <!-- Header -->
    <div class="card">
        <header>
            <div class="title-group">
                <h1>AI On-Device Smart Keyboard OS</h1>
                <p>20-Word Rolling Context, Ghost Text Autocomplete, Text Expander, and Air-Gapped Tone Transformer</p>
            </div>
            <div class="badge-pill" id="hwBadge">
                <span id="hwName">DirectML NPU / CPU</span>
            </div>
        </header>
    </div>

    <!-- Main Sandbox -->
    <div class="card editor-section">
        <div class="toolbar">
            <div class="btn-group">
                <span style="font-size: 0.78rem; color: var(--text-secondary); margin-right: 0.25rem;">Tone Transformer:</span>
                <button class="tone-btn" onclick="applyTone('professional')">Make Professional</button>
                <button class="tone-btn" onclick="applyTone('casual')">Make Casual</button>
                <button class="tone-btn" onclick="applyTone('concise')">Make Concise</button>
            </div>
            <div class="btn-group" style="align-items: center;">
                <div style="display: flex; align-items: center; gap: 0.5rem; background: rgba(255,255,255,0.04); padding: 0.25rem 0.65rem; border-radius: 8px; border: 1px solid var(--card-border);">
                    <span style="font-size: 0.76rem; color: var(--text-secondary); white-space: nowrap;">Filter Conf:</span>
                    <input type="range" id="confSlider" min="50" max="99" value="95" step="1" oninput="updateConfidence(this.value)" style="accent-color: #3b82f6; cursor: pointer; width: 85px;">
                    <span id="confDisplay" style="font-size: 0.8rem; font-weight: 700; color: #60a5fa; min-width: 32px;">95%</span>
                </div>
                <button class="primary" onclick="loadSnippetDemo()">Demo //meet</button>
                <button class="primary" onclick="loadRealWordDemo()">Demo meat->meet</button>
                <button onclick="clearEditor()">Clear</button>
            </div>
        </div>

        <div class="editor-wrapper">
            <textarea id="editor" placeholder="Type sentences (e.g. 'I will meat you at the' or '//meet' or 'I went to the parck')..."></textarea>
        </div>

        <!-- Ghost Text Suggestion Bar -->
        <div class="ghost-bar" id="ghostBar">
            <span>Next-Word Ghost Prediction: <span class="ghost-preview" id="ghostText">--</span></span>
            <span>Press <kbd>Right Arrow</kbd> to autocomplete</span>
        </div>

        <!-- Privacy Alert Pill -->
        <div class="privacy-alert" id="privacyAlert">
            <span id="privacyMsg">[PRIVACY ALERT] Potential confidential credential or token detected.</span>
            <button onclick="redactEditor()" style="background: rgba(239,68,68,0.2); border-color: rgba(239,68,68,0.4); color: #fca5a5;">Redact Locally</button>
        </div>

        <!-- Revert Alert Pill -->
        <div class="revert-indicator" id="revertBanner">
            <span id="revertText">Tab Revert Armed: Press <kbd>Tab</kbd> to restore original text</span>
            <span style="font-size: 0.72rem;">(Active for 3.5s)</span>
        </div>

        <!-- Metrics Strip -->
        <div class="metrics-strip">
            <div class="metric-box">
                <span class="label">Inference Latency</span>
                <span class="val green" id="latencyVal">-- ms</span>
            </div>
            <div class="metric-box">
                <span class="label">Confidence</span>
                <span class="val blue" id="confVal">-- %</span>
            </div>
            <div class="metric-box">
                <span class="label">Corrections Made</span>
                <span class="val" id="correctCount">0</span>
            </div>
            <div class="metric-box">
                <span class="label">Reverts (Tab)</span>
                <span class="val amber" id="revertCount">0</span>
            </div>
        </div>
    </div>

    <!-- Event Stream Log -->
    <div class="card log-section">
        <h3>Live Event Stream</h3>
        <div class="log-container" id="logList">
            <div class="log-item">Engine initialized with 20-word context and Ghost Text. Ready for typing.</div>
        </div>
    </div>
</div>

<script>
    const editor = document.getElementById('editor');
    const latencyVal = document.getElementById('latencyVal');
    const confVal = document.getElementById('confVal');
    const correctCount = document.getElementById('correctCount');
    const revertCount = document.getElementById('revertCount');
    const revertBanner = document.getElementById('revertBanner');
    const revertText = document.getElementById('revertText');
    const logList = document.getElementById('logList');
    const hwName = document.getElementById('hwName');
    const hwBadge = document.getElementById('hwBadge');
    const ghostText = document.getElementById('ghostText');
    const privacyAlert = document.getElementById('privacyAlert');

    let totalCorrections = 0;
    let totalReverts = 0;
    let undoArmed = false;
    let undoTimer = null;
    let currentGhostPrediction = '';

    // Load initial hardware status
    fetch('/api/status')
        .then(r => r.json())
        .then(data => {
            const dev = data.active_provider.replace('ExecutionProvider', '');
            hwName.textContent = `${dev} (${data.is_npu_or_gpu ? 'NPU/GPU' : 'CPU AVX2'})`;
            if (!data.is_npu_or_gpu) hwBadge.classList.add('cpu');
        });

    editor.addEventListener('keydown', async (e) => {
        // 1. Right Arrow or Tab (when not undoing) accepts Ghost Text
        if (e.key === 'ArrowRight' && currentGhostPrediction) {
            e.preventDefault();
            const pos = editor.selectionStart;
            const text = editor.value;
            const before = text.substring(0, pos);
            const after = text.substring(pos);
            const needsSpace = before.length > 0 && !before.endsWith(' ');
            const insertText = (needsSpace ? ' ' : '') + currentGhostPrediction + ' ';
            editor.value = before + insertText + after;
            editor.selectionStart = editor.selectionEnd = before.length + insertText.length;
            addLog(`Ghost autocomplete accepted: <span class="highlight">'${currentGhostPrediction}'</span>`);
            currentGhostPrediction = '';
            ghostText.textContent = '--';
            return;
        }

        // 2. Handle TAB Revert
        if (e.key === 'Tab') {
            e.preventDefault();
            if (undoArmed) {
                const res = await fetch('/api/revert', { method: 'POST' });
                const data = await res.json();
                if (data.reverted) {
                    const text = editor.value;
                    const pos = editor.selectionStart;
                    const before = text.substring(0, pos);
                    const after = text.substring(pos);
                    
                    const eraseLen = data.corrected.length + data.delimiter.length;
                    const newBefore = before.substring(0, before.length - eraseLen) + data.original + data.delimiter;
                    editor.value = newBefore + after;
                    editor.selectionStart = editor.selectionEnd = newBefore.length;

                    totalReverts++;
                    revertCount.textContent = totalReverts;
                    disarmUndo();
                    addLog(`Restored '${data.corrected}' -> '${data.original}' via [TAB]`, 'reverted');
                }
            } else if (currentGhostPrediction) {
                // If no undo active, Tab accepts Ghost Text
                const pos = editor.selectionStart;
                const text = editor.value;
                const before = text.substring(0, pos);
                const after = text.substring(pos);
                const needsSpace = before.length > 0 && !before.endsWith(' ');
                const insertText = (needsSpace ? ' ' : '') + currentGhostPrediction + ' ';
                editor.value = before + insertText + after;
                editor.selectionStart = editor.selectionEnd = before.length + insertText.length;
                addLog(`Ghost autocomplete accepted: <span class="highlight">'${currentGhostPrediction}'</span>`);
                currentGhostPrediction = '';
                ghostText.textContent = '--';
            }
            return;
        }

        // 3. Handle Space / Delimiters for Autocorrect & Snippets
        if (e.key === ' ' || e.key === 'Enter' || e.key === '.' || e.key === ',' || e.key === '!' || e.key === '?') {
            const delim = e.key === 'Enter' ? '\\n' : e.key;
            const text = editor.value;
            const pos = editor.selectionStart;
            const beforeCursor = text.substring(0, pos);
            const words = beforeCursor.trim().split(/\\s+/);
            const currentWord = words[words.length - 1];
            const precedingWords = words.slice(Math.max(0, words.length - 21), words.length - 1).join(' ');

            if (currentWord && currentWord.length > 0) {
                fetch('/api/evaluate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        word: currentWord,
                        delimiter: delim,
                        context: precedingWords
                    })
                })
                .then(r => r.json())
                .then(result => {
                    latencyVal.textContent = `${result.latency_ms.toFixed(2)} ms`;
                    confVal.textContent = `${(result.confidence * 100).toFixed(1)}%`;

                    if (result.is_corrected) {
                        const curText = editor.value;
                        const curPos = editor.selectionStart;
                        const start = curPos - currentWord.length - 1;
                        
                        const before = curText.substring(0, start);
                        const after = curText.substring(curPos);
                        editor.value = before + result.corrected_word + (delim === '\\n' ? '\\n' : delim) + after;
                        editor.selectionStart = editor.selectionEnd = (before + result.corrected_word + delim).length;

                        totalCorrections++;
                        correctCount.textContent = totalCorrections;
                        armUndo(result.original_word, result.corrected_word);
                        
                        if (result.is_expansion) {
                            addLog(`Snippet expanded: <span class="highlight">'${result.original_word}'</span>`);
                        } else {
                            addLog(`Corrected: <span class="highlight">'${result.original_word}' -> '${result.corrected_word}'</span> <span class="latency">(${result.latency_ms.toFixed(2)}ms, ${(result.confidence * 100).toFixed(1)}%)</span>`);
                        }
                    }

                    // Trigger Next-Word Ghost Prediction
                    updateGhostPrediction();
                });
            }
        }
    });

    editor.addEventListener('input', () => {
        scanPrivacy();
        updateGhostPrediction();
    });

    function updateGhostPrediction() {
        const text = editor.value;
        const pos = editor.selectionStart;
        const beforeCursor = text.substring(0, pos).trim();

        if (beforeCursor.length > 3) {
            fetch('/api/predict_ghost', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ context: beforeCursor })
            })
            .then(r => r.json())
            .then(data => {
                if (data.predictions && data.predictions.length > 0) {
                    currentGhostPrediction = data.predictions[0];
                    ghostText.textContent = currentGhostPrediction;
                } else {
                    currentGhostPrediction = '';
                    ghostText.textContent = '--';
                }
            });
        } else {
            currentGhostPrediction = '';
            ghostText.textContent = '--';
        }
    }

    function scanPrivacy() {
        const text = editor.value;
        fetch('/api/scan_privacy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        })
        .then(r => r.json())
        .then(data => {
            if (data.findings && data.findings.length > 0) {
                privacyAlert.classList.add('show');
            } else {
                privacyAlert.classList.remove('show');
            }
        });
    }

    function redactEditor() {
        const text = editor.value;
        fetch('/api/redact_privacy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        })
        .then(r => r.json())
        .then(data => {
            editor.value = data.redacted;
            privacyAlert.classList.remove('show');
            addLog('Applied local privacy redaction guard.');
        });
    }

    function applyTone(mode) {
        const text = editor.value;
        if (!text.trim()) return;

        fetch('/api/transform_tone', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text, mode: mode })
        })
        .then(r => r.json())
        .then(data => {
            editor.value = data.transformed;
            addLog(`Transformed tone to [${mode.toUpperCase()}]`);
        });
    }

    function armUndo(original, corrected) {
        undoArmed = true;
        revertBanner.classList.add('show');
        revertText.innerHTML = `Tab Revert: Press <kbd>Tab</kbd> to restore '<b>${original}</b>'`;
        clearTimeout(undoTimer);
        undoTimer = setTimeout(disarmUndo, 3500);
    }

    function disarmUndo() {
        undoArmed = false;
        revertBanner.classList.remove('show');
    }

    function addLog(html, className = '') {
        const time = new Date().toLocaleTimeString();
        const item = document.createElement('div');
        item.className = `log-item ${className}`;
        item.innerHTML = `[${time}] ${html}`;
        logList.insertBefore(item, logList.firstChild);
    }

    function clearEditor() {
        editor.value = '';
        currentGhostPrediction = '';
        ghostText.textContent = '--';
        privacyAlert.classList.remove('show');
        disarmUndo();
        fetch('/api/reset', { method: 'POST' });
        addLog('Editor cleared.');
    }

    function loadSnippetDemo() {
        editor.value = 'Please review this //meet ';
        editor.focus();
        editor.selectionStart = editor.selectionEnd = editor.value.length;
        fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: '//meet', delimiter: ' ', context: 'Please review this' })
        })
        .then(r => r.json())
        .then(result => {
            if (result.is_corrected) {
                editor.value = 'Please review this ' + result.corrected_word + ' ';
                totalCorrections++;
                correctCount.textContent = totalCorrections;
                armUndo('//meet', result.corrected_word);
                addLog('Snippet expanded: <span class="highlight">//meet</span>');
            }
        });
    }

    function loadRealWordDemo() {
        editor.value = 'I will meat ';
        editor.focus();
        editor.selectionStart = editor.selectionEnd = editor.value.length;
        fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: 'meat', delimiter: ' ', context: 'I will' })
        })
        .then(r => r.json())
        .then(result => {
            if (result.is_corrected) {
                editor.value = 'I will meet you tomorrow ';
                totalCorrections++;
                correctCount.textContent = totalCorrections;
                armUndo('meat', 'meet');
                addLog('Real-word error corrected: <span class="highlight">meat -> meet</span>');
                updateGhostPrediction();
            }
        });
    }

    function updateConfidence(val) {
        document.getElementById('confDisplay').textContent = val + '%';
        fetch('/api/set_confidence', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ confidence: parseFloat(val) / 100.0 })
        })
        .then(r => r.json())
        .then(data => {
            addLog(`Confidence filter adjusted to <span class="highlight">${val}%</span>`);
        });
    }
</script>
</body>
</html>
"""


class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/status":
            self._send_json(hw_info)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        
        try:
            req_data = json.loads(body) if body else {}
        except:
            req_data = {}

        if self.path == "/api/evaluate":
            word = req_data.get("word", "")
            delim = req_data.get("delimiter", " ")
            explicit_ctx = req_data.get("context", None)
            
            res = service.evaluate_word(word, delim, explicit_context=explicit_ctx)
            self._send_json({
                "is_corrected": res.is_corrected,
                "original_word": res.original_word,
                "corrected_word": res.corrected_word,
                "delimiter": res.delimiter,
                "confidence": res.confidence,
                "latency_ms": res.latency_ms,
                "device": res.device,
                "explanation": res.explanation,
                "is_expansion": res.is_expansion,
            })
        elif self.path == "/api/predict_ghost":
            ctx = req_data.get("context", "")
            predictions, lat = service.predict_ghost_text(ctx, top_k=1)
            self._send_json({"predictions": predictions, "latency_ms": lat})
        elif self.path == "/api/transform_tone":
            text = req_data.get("text", "")
            mode = req_data.get("mode", "professional")
            transformed = service.transform_tone(text, mode=mode)
            self._send_json({"transformed": transformed})
        elif self.path == "/api/scan_privacy":
            text = req_data.get("text", "")
            findings = service.scan_privacy(text)
            self._send_json({"findings": findings})
        elif self.path == "/api/redact_privacy":
            text = req_data.get("text", "")
            redacted = service.redact_privacy(text)
            self._send_json({"redacted": redacted})
        elif self.path == "/api/audit_stats":
            stats = service.audit_logger.get_audit_stats()
            self._send_json(stats)
        elif self.path == "/api/revert":
            revert = service.handle_tab_revert()
            if revert:
                self._send_json({
                    "reverted": True,
                    "corrected": revert[0],
                    "original": revert[1],
                    "delimiter": revert[2],
                })
            else:
                self._send_json({"reverted": False})
        elif self.path == "/api/set_confidence":
            val = float(req_data.get("confidence", 0.95))
            if val > 1.0:
                val = val / 100.0
            service.confidence_threshold = val
            self._send_json({"confidence_threshold": service.confidence_threshold})
        elif self.path == "/api/reset":
            service.reset()
            self._send_json({"status": "reset_complete"})
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        pass


def run_server(port=8000, confidence_threshold=None):
    if confidence_threshold is not None:
        eff = confidence_threshold / 100.0 if confidence_threshold > 1.0 else confidence_threshold
        service.confidence_threshold = eff

    server = HTTPServer(("127.0.0.1", port), RequestHandler)
    print(f"\n[SERVER] NeuraType Web Sandbox running at: http://127.0.0.1:{port}")
    print(f"[SERVER] Active Confidence Filter Threshold: {service.confidence_threshold:.1%}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NeuraType Local Web Sandbox")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port to run web server on (default: 8000)")
    parser.add_argument(
        "-c", "--confidence", "--conf",
        type=float,
        default=None,
        help="Custom confidence threshold (e.g. 0.95 or 95). Defaults to policy.yaml value.",
    )
    args, _ = parser.parse_known_args()
    run_server(port=args.port, confidence_threshold=args.confidence)
