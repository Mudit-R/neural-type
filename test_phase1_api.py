import urllib.request
import json

def post(endpoint, data):
    url = f"http://127.0.0.1:8000/api/{endpoint}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read().decode("utf-8"))

print("\n--- TESTING PHASE 1 SMART KEYBOARD OS CAPABILITIES ---")

# 1. Test Autocorrect & Snippet Expansion
res_snippet = post("evaluate", {"word": "//meet", "delimiter": " ", "context": "Please review this"})
print(f"1. Snippet Expansion (//meet): '{res_snippet['corrected_word'][:50]}...'")

# 2. Test Ghost Text Prediction
res_ghost = post("predict_ghost", {"context": "I want to go to the"})
print(f"2. Next-Word Ghost Prediction: {res_ghost['predictions']} (Latency: {res_ghost['latency_ms']:.2f}ms)")

# 3. Test Tone Transformer
res_tone = post("transform_tone", {"text": "hey team, gotta finish this asap. thx", "mode": "professional"})
print(f"3. Professional Tone Rewrite: '{res_tone['transformed']}'")

# 4. Test Privacy Guard
res_privacy = post("scan_privacy", {"text": "My key is sk-1234567890abcdef1234567890abcdef"})
print(f"4. Privacy Scan Result: Found {len(res_privacy['findings'])} hazard(s) -> {res_privacy['findings'][0]['hazard']}")

print("-------------------------------------------------------\n")
