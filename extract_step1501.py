import json

log_path = r"C:\Users\3moha\.gemini\antigravity\brain\2d72dd3e-a000-482f-a448-035820c71536\.system_generated\logs\transcript_full.jsonl"

code_content = None
with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
            
        step = obj.get("step_index", 0)
        if step == 1501:
            for tc in obj.get("tool_calls", []):
                if tc.get("name") == "write_to_file":
                    code_content = tc["args"]["CodeContent"]
                    break

print("Found Step 1501 code_content! Length:", len(code_content))
print("Start:", repr(code_content[:60]))
print("End:", repr(code_content[-60:]))

with open("noon_signup_hybrid.py", "w", encoding="utf-8") as out:
    out.write(code_content)

print("Successfully restored noon_signup_hybrid.py!")
