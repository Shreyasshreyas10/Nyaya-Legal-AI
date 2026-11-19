import sys
from core.pipeline import run_pipeline

def test_query(query: str, target_lang: str):
    print(f"\n==========================================")
    print(f"Testing Query: {query}")
    print(f"Target Language: {target_lang}")
    print(f"==========================================")
    try:
        res = run_pipeline(query, target_lang=target_lang)
        print(f"Detected Language: {res.get('detected_language')}")
        print(f"Target Language: {res.get('target_language')}")
        print(f"Answer:\n{res.get('answer')}")
        print(f"\nCitation Status: {res.get('citations', {}).get('status')}")
        print("Verified Citations:")
        for cit in res.get('citations', {}).get('verified', []):
            print(f" - {cit.get('citation')}: {cit.get('heading')}")
            print(f"   Snippet: {cit.get('snippet')}")
        print("Unverified Citations:")
        for cit in res.get('citations', {}).get('unverified', []):
            print(f" - {cit.get('citation')}: {cit.get('reason')}")
    except Exception as exc:
        print(f"Error executing query: {exc}")

if __name__ == "__main__":
    queries = [
        ("What is the penalty for developer flat delivery delay under RERA?", "en"),
        ("मेरे बिल्डर ने फ्लैट में देरी की, मुझे क्या मुआवजा मिल सकता है?", "hi"),
        ("ನನ್ನ ಬಿಲ್ಡರ್ ಫ್ಲಾಟ್ ನೀಡಲು ತಡಮಾಡಿದ್ದಾರೆ, ನನಗೆ ಏನು ಪರಿಹಾರ ಸಿಗುತ್ತದೆ?", "kn"),
    ]
    for q, lang in queries:
        test_query(q, lang)
