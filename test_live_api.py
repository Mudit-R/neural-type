import urllib.request
import json

def test_api(ctx, word):
    url = "http://127.0.0.1:8000/api/evaluate"
    payload = json.dumps({"word": word, "delimiter": " ", "context": ctx}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    response = urllib.request.urlopen(req)
    res = json.loads(response.read().decode("utf-8"))
    print(f"Context: '{ctx}' | Typed: '{word}' -> Result: '{res['corrected_word']}' (Latency: {res['latency_ms']:.2f}ms, Conf: {res['confidence']*100:.1f}%)")

if __name__ == "__main__":
    print("\n--- Testing Live Server Context & Real-Word Corrections ---")
    test_api("I will", "meat")
    test_api("I ate a", "peace")
    test_api("I bought a", "pare")
    test_api("Please check the", "calender")
    test_api("Yesterday when the weather was sunny and warm we decided to take our bicycle for a long ride to the", "parck")
    print("-----------------------------------------------------------\n")
