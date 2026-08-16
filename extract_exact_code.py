import json

log_path = r"C:\Users\3moha\.gemini\antigravity\brain\2d72dd3e-a000-482f-a448-035820c71536\.system_generated/logs/transcript.jsonl"

code_558 = ""
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
                    code_558 = tc.get("args", {}).get("CodeContent", "")
                    break

print("Step 558 initial code length:", len(code_558))

# Now let's trace step 594, 636, 680, 707
with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
            
        step = obj.get("step_index", 0)
        if step in [594, 636, 680, 707]:
            for tc in obj.get("tool_calls", []):
                if tc.get("name") == "replace_file_content":
                    args = tc.get("args", {})
                    target = args.get("TargetContent", "")
                    replacement = args.get("ReplacementContent", "")
                    if target in code_558:
                        code_558 = code_558.replace(target, replacement)
                        print(f"Applied edit from step {step}")
                    else:
                        print(f"FAILED to apply edit from step {step}!")

print("Final reconstructed code length:", len(code_558))

with open("noon_signup_hybrid.py", "w", encoding="utf-8") as out:
    out.write(code_558)

print("Overwritten noon_signup_hybrid.py with exact step 715 content!")
