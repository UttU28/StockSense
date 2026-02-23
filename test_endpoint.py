import requests
import json
import sys

URL = "http://localhost:7777/v1/chat/completions"

def test_analyze_stock(symbol="META"):
    print(f"Testing Analysis for {symbol}...")
    
    payload = {
        "model": "stock-gita-model",
        "messages": [
            {"role": "user", "content": f"Analyze {symbol}"}
        ]
    }
    
    try:
        response = requests.post(URL, json=payload, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            print("\n--- RESPONSE CONTENT ---\n")
            print(content)
            print("\n------------------------\n")
            
            # Validation
            if "PHASE 0" in content and "PHASE 10" in content:
                print("✅ PASSED: All 11 Phases detected.")
            else:
                print("⚠️ WARNING: Some phases might be missing.")
                
        else:
            print("❌ FAILED")
            print(response.text)
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "META"
    test_analyze_stock(symbol)
