import json, ast

log_path = r"C:\Users\3moha\.gemini\antigravity\brain\2d72dd3e-a000-482f-a448-035820c71536\.system_generated/logs/transcript.jsonl"

code_raw = ""
with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
            
        step = obj.get("step_index", 0)
        if step == 558:
            for tc in obj.get("tool_calls", []):
                if tc.get("name") == "write_to_file":
                    code_raw = tc.get("args", {}).get("CodeContent", "")
                    break

# Safely evaluate python string literal
try:
    clean_code = ast.literal_eval(code_raw)
except Exception as e:
    print("Literal eval error:", e)
    clean_code = code_raw

print("Clean code length:", len(clean_code))
print("First 200 chars:")
print(clean_code[:200])

with open("noon_signup_hybrid.py", "w", encoding="utf-8") as out:
    out.write(clean_code)

print("Saved cleanly unescaped python code!")
