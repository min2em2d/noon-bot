import re

print("Searching HAR file for raw modal text...")
try:
    with open("account.noon.com.har", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        
    # Search for "Add phone number" or "New phone number" surrounding context
    matches = [m.start() for m in re.finditer(r'Add phone number|New phone number', content, re.IGNORECASE)]
    print(f"Found {len(matches)} matches.")
    for idx, pos in enumerate(matches[:5]):
        print(f"\n--- Match {idx} Context ---")
        print(content[pos - 200: pos + 500])
except Exception as e:
    print("Error:", e)
